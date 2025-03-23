import streamlit as st
from agents import create_agent_workflow, transition
from hospital_finder import HospitalFinder
from groq_llm import GroqLLM
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import re
from random import randint

st.set_page_config(page_title="Healthcare Navigator", layout="wide")

def initialize_session_state():
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {}
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 'intake'
    if 'assessment_complete' not in st.session_state:
        st.session_state.assessment_complete = False
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = 'intake'
    if 'hospitals_found' not in st.session_state:
        st.session_state.hospitals_found = []

def display_patient_analytics():
    """
    Display patient analytics based on the actual patient data.
    """
    st.subheader("Patient Analytics Dashboard")
    
    patient_data = st.session_state.patient_data
    
    # Extract data for visualizations
    name = patient_data.get('name', 'Patient')
    pain_level = patient_data.get('pain_level', 5)
    primary_complaints = patient_data.get('primary_complaints', '')
    duration = patient_data.get('duration', 'Unknown')
    symptom_frequency = patient_data.get('symptom_frequency', 'Unknown')
    
    # Create three columns for high-level metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Pain Level", f"{pain_level}/10", delta=None)
        
    with col2:
        st.metric("Symptom Duration", duration, delta=None)
        
    with col3:
        st.metric("Frequency", symptom_frequency, delta=None)
    
    # Main visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Pain assessment visualization based on actual pain level
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = pain_level,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Pain Assessment"},
            gauge = {
                'axis': {'range': [0, 10]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 3], 'color': "green"},
                    {'range': [3, 7], 'color': "yellow"},
                    {'range': [7, 10], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': pain_level
                }
            }
        ))
        
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Treatment impact visualization
        impact_factors = {
            "Rest": min(max(8 - pain_level, 1), 10),
            "Medication": min(max(7 - pain_level + 3, 1), 10),
            "Physical Therapy": min(max(9 - pain_level + 1, 1), 10),
            "Lifestyle Change": min(max(6 - pain_level + 2, 1), 10)
        }
        
        fig = go.Figure([go.Bar(
            x=list(impact_factors.values()),
            y=list(impact_factors.keys()),
            orientation='h',
            marker={'color': ['#4285F4', '#34A853', '#FBBC05', '#EA4335']}
        )])
        
        fig.update_layout(
            title="Estimated Treatment Impact",
            xaxis_title="Effectiveness Score (1-10)",
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Symptom analysis from primary complaints
     # Symptom analysis from primary complaints
    st.subheader("Symptom Analysis")
    
    # Extract keywords from primary complaints
    # Common symptom keywords
    symptom_keywords = [
        "pain", "ache", "sore", "discomfort", "fatigue", "tired", 
        "headache", "nausea", "dizzy", "cough", "fever", "swelling",
        "rash", "itch", "burning", "cramp", "stiff", "weak",
        "numbness", "tingling", "pressure", "difficulty", "stress"
    ]
    
    # Count occurrences of symptom keywords
    word_counts = {}
    for keyword in symptom_keywords:
        count = len(re.findall(r'\b' + keyword + r'\b', primary_complaints.lower()))
        if count > 0:
            word_counts[keyword] = count
    
    # If no keywords found, add placeholders
    if not word_counts:
        word_counts = {
            "discomfort": 1,
            "pain": 1
        }
    
    # Sort keywords by count (descending)
    sorted_symptoms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Use a horizontal bar chart for better readability
    symptom_names = [item[0].capitalize() for item in sorted_symptoms]
    symptom_counts = [item[1] for item in sorted_symptoms]
    
    # Create a color scale based on frequency
    colors = [f"rgba(66, 133, 244, {0.4 + (0.6 * count/max(symptom_counts))})" for count in symptom_counts]
    
    fig = go.Figure(go.Bar(
        x=symptom_counts,
        y=symptom_names,
        orientation='h',
        marker_color=colors,
        text=symptom_counts,
        textposition='auto'
    ))
    
    fig.update_layout(
        title="Symptoms Mentioned in Patient Description",
        xaxis_title="Frequency",
        yaxis_title="Symptom",
        height=max(250, len(symptom_names) * 30),  # Dynamic height based on number of symptoms
        margin=dict(l=20, r=20, t=50, b=30)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add symptom clustering/categorization
    if len(word_counts) > 1:
        st.subheader("Symptom Categories")
        
        # Define symptom categories
        categories = {
            "Pain-related": ["pain", "ache", "sore", "burning", "cramp", "stiff"],
            "Respiratory": ["cough", "difficulty", "pressure"],
            "Neurological": ["headache", "dizzy", "numbness", "tingling"],
            "Gastrointestinal": ["nausea", "discomfort"],
            "Skin-related": ["rash", "itch", "swelling"],
            "General": ["fatigue", "tired", "weak", "fever", "stress"]
        }
        
        # Count symptoms by category
        category_counts = {}
        for category, keywords in categories.items():
            count = sum(word_counts.get(keyword, 0) for keyword in keywords)
            if count > 0:
                category_counts[category] = count
        
        # Create pie chart for symptom categories
        if category_counts:
            fig = go.Figure(data=[go.Pie(
                labels=list(category_counts.keys()),
                values=list(category_counts.values()),
                hole=.3,
                marker_colors=px.colors.qualitative.Safe
            )])
            
            fig.update_layout(
                title="Symptom Categories",
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Recovery timeline projection
    st.subheader("Recovery Timeline Projection")
    
    # Generate a recovery timeline based on pain level and other factors
    # Higher pain level = longer projected recovery
    weeks = max(3, min(12, int(pain_level * 1.5)))
    recovery_stages = [
        "Initial Treatment",
        "Symptom Management",
        "Improvement Phase",
        "Functional Recovery",
        "Full Recovery"
    ]
    
    # Create equal stages throughout the timeline
    stage_weeks = [max(1, int(weeks / len(recovery_stages)))] * len(recovery_stages)
    # Ensure the total adds up to the projected weeks
    stage_weeks[-1] += weeks - sum(stage_weeks)
    
    # Create cumulative weeks for each stage
    cumulative_weeks = [sum(stage_weeks[:i+1]) for i in range(len(stage_weeks))]
    
    # Create the timeline
    fig = go.Figure()
    
    for i, stage in enumerate(recovery_stages):
        # Calculate bars
        start_week = 0 if i == 0 else cumulative_weeks[i-1]
        end_week = cumulative_weeks[i]
        
        fig.add_trace(go.Bar(
            x=[end_week - start_week],
            y=[0],
            base=[start_week],
            orientation='h',
            name=stage,
            text=[stage],
            textposition='inside',
            insidetextanchor='middle',
            hoverinfo='text',
            hovertext=f"{stage}: {end_week - start_week} week(s)"
        ))
    
    # Add current week marker
    fig.add_shape(
        type="line",
        x0=0, y0=-0.4,
        x1=0, y1=0.4,
        line=dict(color="red", width=3),
        name="Current"
    )
    
    fig.add_annotation(
        x=0, y=-0.5,
        text="Current",
        showarrow=False,
        font=dict(color="red")
    )
    
    fig.update_layout(
        title=f"Projected Recovery Timeline: {weeks} Weeks",
        xaxis_title="Weeks",
        showlegend=False,
        barmode='stack',
        height=200,
        yaxis={"visible": False},
        margin=dict(l=20, r=20, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    initialize_session_state()
    
    st.title("Healthcare Navigator")
    
    # Sidebar for navigation and status
    with st.sidebar:
        st.title("Navigation")
        st.write(f"Current Stage: {st.session_state.current_stage.title()}")
        st.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        st.write(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        st.subheader("Additional Tools")
        if st.sidebar.button("Find Healthcare Providers"):
            st.session_state.current_stage = 'hospital_finder'
    
    # Progress bar
    stages = {'intake': 1, 'assessment': 2, 'care_planning': 3}
    current_progress = stages.get(st.session_state.current_stage, 1)
    st.progress(current_progress/3)
    
    # Route to appropriate stage
    if st.session_state.current_stage == 'intake':
        intake_form()
    elif st.session_state.current_stage == 'assessment':
        clinical_assessment()
    elif st.session_state.current_stage == 'care_planning':
        care_planning()
    elif st.session_state.current_stage == 'hospital_finder': 
        hospital_finder = HospitalFinder()
        hospital_finder.render_hospital_finder()

def intake_form():
    st.header("Patient Intake Form")
    
    with st.form("intake_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*")
            contact = st.text_input("Contact Number*")
            min_date = datetime(1900, 1, 1)  # Allow dates back to 1900
            max_date = datetime.now()        # Today as the maximum
            dob = st.date_input("Date of Birth", value=datetime(2000, 1, 1), min_value=min_date, max_value=max_date)
        
        with col2:
            emergency_contact = st.text_input("Emergency Contact*")
            emergency_relation = st.text_input("Emergency Contact Relation")
            gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"])
        
        st.markdown("### Medical Information")
        primary_complaints = st.text_area("What brings you in today? Please describe your symptoms*")
        existing_conditions = st.text_area("Any existing medical conditions?")
        current_medications = st.text_area("Current medications (if any)")
        
        # Insurance information
        st.markdown("### Insurance Information")
        insurance_provider = st.text_input("Insurance Provider")
        insurance_id = st.text_input("Insurance ID/Member Number")
        
        # Location Information
        st.markdown("### Location Information")
        hospital_finder = HospitalFinder()
        hospital_finder.add_to_intake_form()
        
        submit = st.form_submit_button("Submit Intake Form")
        
        if submit:
            if not (name and contact and emergency_contact and primary_complaints):
                st.error("Please fill in all required fields")
                return
                
            with st.spinner("Processing intake information..."):
                try:
                    # Get location data from the hospital finder
                    location_data = {
                        "address": st.session_state.patient_data.get("address", ""),
                        "city": st.session_state.patient_data.get("city", ""),
                        "state": st.session_state.patient_data.get("state", ""),
                        "zipcode": st.session_state.patient_data.get("zipcode", ""),
                        "location_str": st.session_state.patient_data.get("location_str", "")
                    }
                    
                    # Initialize state
                    initial_state = {
                        "patient_data": {
                            "name": name,
                            "contact": contact,
                            "dob": str(dob),
                            "emergency_contact": emergency_contact,
                            "emergency_relation": emergency_relation,
                            "gender": gender,
                            "primary_complaints": primary_complaints,
                            "existing_conditions": existing_conditions,
                            "current_medications": current_medications,
                            "insurance_provider": insurance_provider,
                            "insurance_id": insurance_id,
                            "address": location_data["address"],
                            "city": location_data["city"],
                            "state": location_data["state"],
                            "zipcode": location_data["zipcode"],
                            "location_str": location_data["location_str"],
                            "intake_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        },
                        "stage": "intake"
                    }
                    
                    workflow, conditions = create_agent_workflow()
                    result = transition(workflow, initial_state, conditions)
                    
                    if isinstance(result, dict) and 'patient_data' in result:
                        st.session_state.patient_data.update(result['patient_data'])
                        st.session_state.current_stage = 'assessment'
                        st.rerun()
                    else:
                        st.error("Failed to process intake information")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def clinical_assessment():
    st.header("Clinical Assessment")
    
    with st.form("assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            pain_level = st.slider("Pain Level (1-10)", 1, 10, 5)
            duration = st.text_input("Duration of Symptoms*")
        
        with col2:
            symptom_frequency = st.selectbox(
                "Symptom Frequency*",
                ["Select", "Constant", "Daily", "Weekly", "Monthly", "Occasionally"]
            )
            symptoms_worsen = st.text_area("What makes symptoms worse?")
        
        st.markdown("### Treatment History")
        previous_treatment = st.text_area("Previous treatments tried")
        medications_tried = st.text_area("Medications tried")
        
        submit = st.form_submit_button("Complete Assessment")
        
        if submit:
            if not (duration and symptom_frequency != "Select"):
                st.error("Please fill in all required fields")
                return
                
            with st.spinner("Processing assessment..."):
                try:
                    assessment_state = {
                        "patient_data": {
                            **st.session_state.patient_data,
                            "pain_level": pain_level,
                            "duration": duration,
                            "symptom_frequency": symptom_frequency,
                            "symptoms_worsen": symptoms_worsen,
                            "previous_treatment": previous_treatment,
                            "medications_tried": medications_tried,
                            "assessment_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        },
                        "stage": "assessment"
                    }
                    
                    workflow, conditions = create_agent_workflow()
                    result = transition(workflow, assessment_state, conditions)
                    
                    if isinstance(result, dict) and 'patient_data' in result:
                        st.session_state.patient_data.update(result['patient_data'])
                        st.session_state.current_stage = 'care_planning'
                        st.rerun()
                    else:
                        st.error("Failed to process assessment")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

def care_planning():
    st.header("Care Planning")
    
    if 'care_plan_complete' not in st.session_state.patient_data:
        with st.spinner("Generating care plan..."):
            try:
                planning_state = {
                    "patient_data": st.session_state.patient_data,
                    "stage": "care_planning"
                }
                
                workflow, conditions = create_agent_workflow()
                result = transition(workflow, planning_state, conditions)
                
                if isinstance(result, dict) and 'patient_data' in result:
                    st.session_state.patient_data.update(result['patient_data'])
                else:
                    st.error("Failed to generate care plan")
                    return
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                return
    
    # Display patient information
    st.subheader("Patient Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Name:** {st.session_state.patient_data.get('name', 'N/A')}")
        st.write(f"**Contact:** {st.session_state.patient_data.get('contact', 'N/A')}")
        st.write(f"**Date of Birth:** {st.session_state.patient_data.get('dob', 'N/A')}")
    
    with col2:
        st.write(f"**Emergency Contact:** {st.session_state.patient_data.get('emergency_contact', 'N/A')}")
        st.write(f"**Relation:** {st.session_state.patient_data.get('emergency_relation', 'N/A')}")
        st.write(f"**Gender:** {st.session_state.patient_data.get('gender', 'N/A')}")
    
    # Display location information if available
    if (st.session_state.patient_data.get('city') or 
        st.session_state.patient_data.get('state') or 
        st.session_state.patient_data.get('zipcode')):
        
        st.write(f"**Location:** {st.session_state.patient_data.get('location_str', 'N/A')}")
    
    # Display risk assessment
    st.subheader("Risk Assessment")
    st.write(st.session_state.patient_data.get("risk_assessment", "No risk assessment available"))
    
    # Display clinical assessment
    st.subheader("Clinical Assessment")
    st.write(st.session_state.patient_data.get("clinical_assessment", "No clinical assessment available"))
    
    # Add medical imaging section if available
    if "medical_images" in st.session_state.patient_data and st.session_state.patient_data["medical_images"]:
        st.subheader("Medical Imaging Results")
        
        for img in st.session_state.patient_data["medical_images"]:
            with st.expander(f"{img['type']} - {img['body_region']} ({img['date']})"):
                st.write("**Key Findings:**")
                st.write(img["key_findings"])
    
    # Display treatment recommendations
    st.subheader("Treatment Recommendations")
    st.write(st.session_state.patient_data.get("treatment_recommendations", "No recommendations available"))
    
    # Display recommended healthcare providers
    hospital_finder = HospitalFinder()
    hospital_finder.integrate_with_care_planning()
    
    # Display care level with appropriate color
    care_level = st.session_state.patient_data.get("care_level", "Not determined")
    care_colors = {
        "Routine": "#28a745",
        "Urgent": "#ffc107",
        "Emergency": "#dc3545"
    }
    care_color = care_colors.get(care_level, "#6c757d")
    
    st.markdown(
        f"""
        <div style='
            padding: 20px;
            border-radius: 10px;
            background-color: {care_color};
            color: white;
            text-align: center;
            margin: 20px 0;
        '>
            <h3 style='margin: 0;'>Care Level: {care_level}</h3>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add visualization toggle
    if st.checkbox("Show Patient Analytics Dashboard", value=False):
        display_patient_analytics()
    
    # Add model comparison
    model_comparison()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF report..."):
                try:
                    from pdf_generator import PDFGenerator
                    pdf_gen = PDFGenerator()
                    pdf_buffer = pdf_gen.create_medical_report(st.session_state.patient_data)
                    
                    st.download_button(
                        label="Download Medical Report",
                        data=pdf_buffer,
                        file_name=f"medical_report_{st.session_state.patient_data['name'].replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("PDF Report Generated Successfully!")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
    
    with col2:
        if st.button("Find Healthcare Providers", key="find_providers_btn"):
            st.session_state.previous_stage = 'care_planning'
            st.session_state.current_stage = 'hospital_finder'
            st.rerun()
    
    with col3:
        if st.button("Start New Assessment"):
            st.session_state.clear()
            st.rerun()

def model_comparison():
    st.subheader("AI Model Comparison")
    
    with st.expander("Compare different AI models for assessment"):
        # Sample symptoms for comparison
        sample_query = st.text_area(
            "Enter symptoms for comparison", 
            value="Patient presents with severe headache, sensitivity to light, and nausea for the past 3 days."
        )
        
        if st.button("Compare Models"):
            with st.spinner("Comparing models..."):
                try:
                    llm = GroqLLM()
                    system_prompt = "You are a medical expert. Provide a detailed clinical assessment of these symptoms with the following sections: 1) Detailed Symptom Analysis, 2) Risk Level Determination, 3) Recommended Additional Screenings or Tests, 4) Potential Diagnoses, and 5) Areas Requiring Immediate Attention. Use markdown formatting with headers, bullet points, and asterisks."
                    results = llm.compare_models(sample_query, system_prompt)
                    
                    # Display comparison
                    for model_name, result in results.items():
                        with st.container():
                            st.markdown(f"### {model_name.title()} Model")
                            st.markdown(f"**Response time:** {result['elapsed_time']:.2f} seconds")
                            
                            # Display the assessment content
                            st.markdown("**Assessment:**")
                            st.markdown(result['content'])
                            
                            st.divider()
                            
                except Exception as e:
                    st.error(f"Error during model comparison: {str(e)}")

if __name__ == "__main__":
    main()