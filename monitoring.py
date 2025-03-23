import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import re
from collections import Counter
import numpy as np
import pandas as pd
import math

class EnhancedMonitoringDashboard:
    """Advanced patient analytics dashboard with clinical insights"""
    
    def __init__(self):
        # Use only actual patient data
        self.patient_data = st.session_state.patient_data if 'patient_data' in st.session_state else {}
        
        # Extract key metrics for analysis
        self._extract_key_metrics()
    
    def _extract_key_metrics(self):
        """Extract and calculate key metrics from patient data"""
        if not self.patient_data:
            return
            
        # Basic demographics
        self.age = self._extract_age_from_dob(self.patient_data.get('dob', ''))
        self.gender = self.patient_data.get('gender', 'Unknown')
        self.pain_level = self.patient_data.get('pain_level', None)
        
        # Symptom duration in days (convert various formats to numeric days)
        duration_str = self.patient_data.get('duration', '').lower()
        self.duration_days = self._parse_duration(duration_str)
        
        # Extract symptom keywords
        self.primary_complaints = self.patient_data.get('primary_complaints', '')
        self.symptoms = self._analyze_symptoms()
        
        # Calculate clinical risk score (0-100)
        self.risk_score = self._calculate_risk_score()
        
        # Generate treatment response prediction
        self.treatment_response = self._predict_treatment_response()
        
        # Determine patient journey stage
        self.journey_stage = self._determine_journey_stage()
    
    def _extract_age_from_dob(self, dob_str):
        """Extract age from date of birth string"""
        try:
            # Parse the DOB string to a datetime object
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            # Calculate age
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age
        except:
            return None
    
    def _parse_duration(self, duration_str):
        """Convert duration string to approximate days"""
        if not duration_str:
            return None
            
        duration_str = duration_str.lower()
        days = 0
        
        # Extract numbers using regex
        numbers = re.findall(r'\d+', duration_str)
        if not numbers:
            return None
            
        num = int(numbers[0])
        
        # Convert to days based on units
        if 'day' in duration_str:
            days = num
        elif 'week' in duration_str:
            days = num * 7
        elif 'month' in duration_str:
            days = num * 30
        elif 'year' in duration_str:
            days = num * 365
        elif 'hour' in duration_str:
            days = max(1, round(num / 24))  # Minimum 1 day
            
        return days
    
    def _analyze_symptoms(self):
        """Analyze symptoms from patient complaints"""
        symptom_keywords = [
            "pain", "ache", "sore", "discomfort", "fatigue", "tired", 
            "headache", "nausea", "dizzy", "cough", "fever", "swelling",
            "rash", "itch", "burning", "cramp", "stiff", "weak",
            "numbness", "tingling", "pressure", "difficulty", "stress",
            "vomit", "diarrhea", "constipation", "bleeding", "breath",
            "sleep", "appetite", "thirst", "vision", "hearing"
        ]
        
        # Count occurrences of symptom keywords in current patient data
        word_counts = Counter()
        
        if self.primary_complaints:
            for keyword in symptom_keywords:
                count = len(re.findall(r'\b' + keyword + r'\b', self.primary_complaints.lower()))
                if count > 0:
                    word_counts[keyword] = count
        
        return word_counts
    
    def _calculate_risk_score(self):
        """Calculate a clinical risk score based on available data"""
        if not self.patient_data:
            return None
            
        score = 50  # Baseline score
        
        # Adjust based on pain level
        if self.pain_level is not None:
            if self.pain_level >= 8:
                score += 15
            elif self.pain_level >= 5:
                score += 7
            
        # Adjust based on symptom duration
        if self.duration_days is not None:
            if self.duration_days > 14:
                score += 10
            elif self.duration_days > 7:
                score += 5
                
        # Adjust based on age (higher risk for very young and elderly)
        if self.age is not None:
            if self.age < 12 or self.age > 65:
                score += 8
                
        # Adjust based on important symptoms
        high_risk_symptoms = ["fever", "breathing", "chest", "unconscious", "breath", "dizzy"]
        for symptom in high_risk_symptoms:
            if symptom in self.primary_complaints.lower():
                score += 10
                break
                
        # Cap score at 100
        return min(100, score)
    
    def _predict_treatment_response(self):
        """Predict treatment response based on patient factors"""
        if not self.patient_data or self.pain_level is None:
            return {}
            
        # Base response rates
        response = {
            "medication": 60,  # 60% base response
            "physical_therapy": 50,
            "surgery": 80,
            "lifestyle": 40,
            "counseling": 45
        }
        
        # Adjust based on pain level (higher pain = lower response to conservative treatment)
        pain_factor = (10 - self.pain_level) / 10
        response["medication"] *= (0.8 + (0.4 * pain_factor))
        response["physical_therapy"] *= (0.7 + (0.6 * pain_factor))
        response["lifestyle"] *= (0.6 + (0.8 * pain_factor))
        
        # Adjust based on duration (chronic conditions respond less to medication)
        if self.duration_days is not None and self.duration_days > 90:
            response["medication"] *= 0.8
            response["physical_therapy"] *= 1.1
            response["counseling"] *= 1.2
            
        # Round values
        for key in response:
            response[key] = round(response[key])
            
        return response
    
    def _determine_journey_stage(self):
        """Determine where the patient is in their care journey"""
        if not self.patient_data:
            return "Intake"
            
        if 'care_plan_complete' in self.patient_data and self.patient_data['care_plan_complete']:
            return "Treatment"
        elif 'assessment_complete' in self.patient_data and self.patient_data['assessment_complete']:
            return "Assessment"
        elif 'intake_complete' in self.patient_data and self.patient_data['intake_complete']:
            return "Triage"
        else:
            return "Intake"
    
    def _create_spider_chart(self):
        """Create a spider/radar chart of patient health dimensions"""
        if not self.patient_data:
            return None
            
        # Define health dimensions to assess
        categories = ['Pain Management', 'Mobility', 'Daily Function', 
                     'Mental Health', 'Sleep Quality', 'Treatment Response']
        
        # Calculate values based on available data
        values = []
        
        # Pain management (inverse of pain level)
        pain_mgmt = 10 - self.pain_level if self.pain_level is not None else 5
        values.append(pain_mgmt)
        
        # Mobility (estimated from complaints and pain level)
        mobility = 7
        if any(term in self.primary_complaints.lower() for term in ['walk', 'mobility', 'movement', 'leg']):
            mobility -= 3
        if self.pain_level and self.pain_level > 6:
            mobility -= 2
        values.append(max(1, mobility))
        
        # Daily function
        daily_function = 8
        if self.pain_level and self.pain_level > 7:
            daily_function -= 3
        if self.duration_days and self.duration_days > 14:
            daily_function -= 2
        values.append(max(1, daily_function))
        
        # Mental health
        mental_health = 7
        if any(term in self.primary_complaints.lower() for term in ['stress', 'anxious', 'worry', 'depress']):
            mental_health -= 3
        if self.pain_level and self.pain_level > 8:
            mental_health -= 2
        values.append(max(1, mental_health))
        
        # Sleep quality
        sleep = 6
        if any(term in self.primary_complaints.lower() for term in ['sleep', 'insomnia', 'tired', 'fatigue']):
            sleep -= 3
        if self.pain_level and self.pain_level > 6:
            sleep -= 2
        values.append(max(1, sleep))
        
        # Treatment response (estimated)
        treatment = 5
        if self.journey_stage == "Treatment":
            treatment = 7
        values.append(treatment)
        
        # Close the loop
        categories.append(categories[0])
        values.append(values[0])
        
        # Create the radar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Current Status'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=False,
            title="Patient Health Dimensions"
        )
        
        return fig
    
    def _create_recovery_projection(self):
        """Create a recovery projection visualization"""
        if not self.patient_data or self.pain_level is None:
            return None
            
        # Estimate recovery timeline based on current pain and duration
        recovery_weeks = max(4, min(24, math.ceil(self.pain_level * 1.5)))
        if self.duration_days and self.duration_days > 90:
            recovery_weeks = max(recovery_weeks, 12)  # Chronic conditions take longer
            
        # Generate data for recovery curve
        weeks = list(range(recovery_weeks + 1))
        
        # Create S-curve for pain reduction using sigmoid function
        midpoint = recovery_weeks / 2
        steepness = 0.5
        pain_values = [self.pain_level * (1 - 1/(1 + math.exp(-steepness * (w - midpoint)))) for w in weeks]
        
        # Create the line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=weeks,
            y=pain_values,
            mode='lines+markers',
            name='Pain Level',
            line=dict(color='#E63946', width=3),
            hovertemplate='Week %{x}: Pain level %{y:.1f}<extra></extra>'
        ))
        
        # Add milestones
        milestones = [
            {"week": 1, "event": "Initial response to treatment", "color": "#1D3557"},
            {"week": round(recovery_weeks * 0.3), "event": "Noticeable improvement", "color": "#457B9D"},
            {"week": round(recovery_weeks * 0.7), "event": "Substantial recovery", "color": "#A8DADC"},
            {"week": recovery_weeks, "event": "Expected full recovery", "color": "#2A9D8F"}
        ]
        
        for milestone in milestones:
            week = milestone["week"]
            if week < len(pain_values):
                fig.add_trace(go.Scatter(
                    x=[week],
                    y=[pain_values[week]],
                    mode='markers',
                    marker=dict(size=12, symbol='star', color=milestone["color"]),
                    name=milestone["event"],
                    hoverinfo='text',
                    hovertext=f"{milestone['event']} (Week {week})"
                ))
        
        # Add current week marker
        fig.add_shape(
            type="line",
            x0=0, x1=0,
            y0=0, y1=self.pain_level,
            line=dict(color="red", width=3, dash="dash"),
        )
        
        fig.add_annotation(
            x=0, y=self.pain_level/2,
            text="Current",
            showarrow=False,
            font=dict(color="red"),
            xanchor="right"
        )
        
        fig.update_layout(
            title=f"Projected Pain Reduction Over {recovery_weeks} Weeks",
            xaxis_title="Weeks",
            yaxis_title="Pain Level",
            yaxis=dict(range=[0, 10]),
            hovermode="closest",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_treatment_response_chart(self):
        """Create a chart showing predicted response to different treatments"""
        if not self.treatment_response:
            return None
            
        # Sort treatments by predicted effectiveness
        sorted_treatments = sorted(self.treatment_response.items(), key=lambda x: x[1], reverse=True)
        
        treatments = [t[0].title() for t in sorted_treatments]
        effectiveness = [t[1] for t in sorted_treatments]
        
        # Create color gradient based on effectiveness values
        colors = ['#' + hex(int(210 - (150 * e/100)))[2:].zfill(2) + 
                  hex(int(60 + (150 * e/100)))[2:].zfill(2) + 
                  '80' for e in effectiveness]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=treatments,
            x=effectiveness,
            orientation='h',
            marker=dict(
                color=effectiveness,
                colorscale='Bluered_r',
                colorbar=dict(title="Response %"),
            ),
            hovertemplate='%{y}: %{x}% response rate<extra></extra>'
        ))
        
        fig.update_layout(
            title="Predicted Treatment Response Rates",
            xaxis_title="Predicted Response (%)",
            yaxis_title="Treatment Approach",
            xaxis=dict(range=[0, 100]),
            height=350
        )
        
        return fig
    
    def _create_symptom_network(self):
        """Create a network visualization of symptom relationships"""
        if not self.symptoms:
            return None
            
        # Create categories for the symptoms
        categories = {
            "Pain-related": ["pain", "ache", "sore", "burning", "cramp", "stiff"],
            "Respiratory": ["cough", "breath", "chest"],
            "Neurological": ["headache", "dizzy", "numbness", "tingling"],
            "Gastrointestinal": ["nausea", "vomit", "diarrhea", "constipation", "appetite"],
            "Skin-related": ["rash", "itch", "swelling"],
            "General": ["fatigue", "tired", "weak", "fever", "stress", "sleep"]
        }
        
        # Count symptoms by category
        category_counts = {}
        for category, keywords in categories.items():
            count = sum(self.symptoms.get(keyword, 0) for keyword in keywords)
            if count > 0:
                category_counts[category] = count
                
        if not category_counts:
            return None
            
        # Color map for categories
        color_map = {
            "Pain-related": "#E63946", 
            "Respiratory": "#1D3557", 
            "Neurological": "#457B9D",
            "Gastrointestinal": "#A8DADC", 
            "Skin-related": "#F1FAEE", 
            "General": "#2A9D8F"
        }
        
        # Create data for the chart
        categories_list = list(category_counts.keys())
        values = list(category_counts.values())
        colors = [color_map.get(cat, "#888888") for cat in categories_list]
        
        # Create links between categories
        source = []
        target = []
        link_value = []
        
        # Connect categories if patient has symptoms in both
        for i, cat1 in enumerate(categories_list):
            for j, cat2 in enumerate(categories_list):
                if i < j:  # Only connect once
                    # Link strength is proportional to symptom counts
                    strength = min(category_counts[cat1], category_counts[cat2]) / 2
                    if strength > 0:
                        source.append(i)
                        target.append(j)
                        link_value.append(strength)
        
        # Create the Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = categories_list,
                color = colors
            ),
            link = dict(
                source = source,
                target = target,
                value = link_value
            )
        )])
        
        fig.update_layout(
            title_text="Symptom Relationship Network",
            font_size=12,
            height=400
        )
        
        return fig
        
    def render_dashboard(self):
        """Render the enhanced patient monitoring dashboard"""
        st.title("Advanced Patient Analytics Dashboard")
        
        # Check if we have patient data
        if not self.patient_data:
            st.warning("No patient data available. Please complete a patient assessment first.")
            return
        
        # Summary risk cards
        st.subheader("Patient Overview")
        
        col1, col2, col3 = st.columns(3)
        
        # Patient basic info 
        with col1:
            name = self.patient_data.get('name', 'Unknown')
            title_case_name = " ".join(word.capitalize() for word in name.split())
            
            st.markdown(f"""
            <div style="border-radius:10px; padding:15px; background-color:#f0f2f6;">
                <h3 style="margin-top:0;">{title_case_name}</h3>
                <p>Age: {self.age if self.age else 'Unknown'}</p>
                <p>Gender: {self.gender}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Clinical risk score
        with col2:
            if self.risk_score is not None:
                # Determine color based on risk score
                if self.risk_score >= 70:
                    risk_color = "#E63946"  # High risk - red
                    risk_level = "High"
                elif self.risk_score >= 40:
                    risk_color = "#F4A261"  # Medium risk - orange
                    risk_level = "Medium"
                else:
                    risk_color = "#2A9D8F"  # Low risk - green
                    risk_level = "Low"
                    
                st.markdown(f"""
                <div style="border-radius:10px; padding:15px; background-color:{risk_color}; color:white;">
                    <h3 style="margin-top:0;">Risk Score: {self.risk_score}</h3>
                    <p>Risk Level: {risk_level}</p>
                    <p>Based on {len(self.symptoms)} symptoms</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="border-radius:10px; padding:15px; background-color:#f0f2f6;">
                    <h3 style="margin-top:0;">Risk Score</h3>
                    <p>Insufficient data</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Care stage journey
        with col3:
            # Define stages and their order
            stages = ["Intake", "Triage", "Assessment", "Treatment", "Follow-up"]
            current_stage_index = stages.index(self.journey_stage) if self.journey_stage in stages else 0
            
            # Create journey visualization
            stage_html = ""
            for i, stage in enumerate(stages):
                if i == current_stage_index:
                    # Current stage
                    stage_html += f'<div style="background-color:#4682B4; color:white; padding:5px; margin:5px; border-radius:5px; text-align:center;"><b>{stage}</b></div>'
                elif i < current_stage_index:
                    # Completed stage
                    stage_html += f'<div style="background-color:#90EE90; color:black; padding:5px; margin:5px; border-radius:5px; text-align:center;">{stage}</div>'
                else:
                    # Future stage
                    stage_html += f'<div style="background-color:#f0f2f6; color:gray; padding:5px; margin:5px; border-radius:5px; text-align:center;">{stage}</div>'
            
            st.markdown(f"""
            <div style="border-radius:10px; padding:15px; background-color:#f0f2f6;">
                <h3 style="margin-top:0;">Patient Journey</h3>
                {stage_html}
            </div>
            """, unsafe_allow_html=True)
        
        # Patient Health Dimensions Spider Chart
        st.subheader("Health Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            spider_chart = self._create_spider_chart()
            if spider_chart:
                st.plotly_chart(spider_chart, use_container_width=True)
            else:
                st.info("Insufficient data for health dimensions analysis.")
        
        with col2:
            # Pain assessment visualization if available
            if self.pain_level is not None:
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = self.pain_level,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Pain Severity"},
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
                            'value': self.pain_level
                        }
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No pain assessment data available.")
        
        # Symptom Analysis
        st.subheader("Symptom Analysis")
        
        if self.symptoms:
            # Advanced symptom visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Symptom frequency bar chart
                sorted_symptoms = sorted(self.symptoms.items(), key=lambda x: x[1], reverse=True)
                
                symptoms = [item[0].capitalize() for item in sorted_symptoms]
                counts = [item[1] for item in sorted_symptoms]
                
                fig = go.Figure(go.Bar(
                    x=counts,
                    y=symptoms,
                    orientation='h',
                    marker=dict(
                        color=counts,
                        colorscale='Viridis',
                    ),
                    hovertemplate='%{y}: %{x} occurrences<extra></extra>'
                ))
                
                fig.update_layout(
                    title="Key Symptoms Identified",
                    xaxis_title="Frequency",
                    yaxis_title="Symptom",
                    height=max(250, len(symptoms) * 30)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Symptom network diagram
                network_chart = self._create_symptom_network()
                if network_chart:
                    st.plotly_chart(network_chart, use_container_width=True)
                else:
                    st.info("Insufficient data for symptom relationship analysis.")
        else:
            st.info("No detailed symptom data available for analysis.")
        
        # Treatment Analysis
        st.subheader("Treatment Analysis & Projections")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Treatment response prediction
            response_chart = self._create_treatment_response_chart()
            if response_chart:
                st.plotly_chart(response_chart, use_container_width=True)
            else:
                st.info("Insufficient data for treatment response prediction.")
        
        with col2:
            # Recovery timeline projection
            recovery_chart = self._create_recovery_projection()
            if recovery_chart:
                st.plotly_chart(recovery_chart, use_container_width=True)
            else:
                st.info("Insufficient data for recovery projection.")
        
        # Care Recommendations
        st.subheader("AI-Enhanced Care Recommendations")
        
        if 'treatment_recommendations' in self.patient_data:
            st.markdown(self.patient_data['treatment_recommendations'])
        else:
            # Generate basic recommendations based on available data
            if self.pain_level is not None and self.primary_complaints:
                st.markdown("""
                ### Preliminary Care Recommendations
                
                Based on the current assessment, consider the following:
                
                * Comprehensive evaluation to determine specific diagnosis
                * Pain management appropriate to severity level
                * Regular monitoring of symptom progression
                * Follow-up reassessment within 1-2 weeks
                
                Please consult with healthcare provider for personalized recommendations.
                """)
            else:
                st.info("Complete the clinical assessment to receive detailed care recommendations.")
        
        # Display care level if available
        if 'care_level' in self.patient_data:
            care_level = self.patient_data.get('care_level', 'Unknown')
            care_colors = {
                "Routine": "#2A9D8F",
                "Urgent": "#F4A261",
                "Emergency": "#E63946",
                "Unknown": "#6c757d"
            }
            
            care_color = care_colors.get(care_level, "#6c757d")
            
            st.markdown(f"""
            <div style='
                padding: 20px;
                border-radius: 10px;
                background-color: {care_color};
                color: white;
                text-align: center;
                margin: 20px 0;
                font-size: 20px;
                font-weight: bold;
            '>
                Current Care Level: {care_level}
            </div>
            """, unsafe_allow_html=True)
            
        # Footer with disclaimer
        st.markdown("""
        ---
        **Disclaimer**: This dashboard provides analytical insights based on available patient data. 
        It is designed for illustrative purposes and should not replace professional medical advice.
        """)

# For direct testing from command line
if __name__ == "__main__":
    dashboard = EnhancedMonitoringDashboard()
    dashboard.render_dashboard()