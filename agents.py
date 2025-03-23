from langgraph.graph import Graph, StateGraph
from groq_llm import GroqLLM
from typing import Dict, TypedDict
import json

llm = GroqLLM()

# Type definitions
class AgentState(TypedDict):
    patient_data: Dict
    stage: str

def route(state: Dict) -> str:
    """Determine the next step in the workflow."""
    stage = state.get('stage', 'intake')
    patient_data = state.get('patient_data', {})

    # First process the current stage
    if stage == 'intake':
        # Process intake first
        state = intake_coordinator(state)
        # Then check if we can move to assessment
        if state['patient_data'].get('intake_complete'):
            return "assessment"
    elif stage == 'assessment':
        # Process assessment first
        state = clinical_assessment(state)
        # Then check if we can move to care_planning
        if state['patient_data'].get('assessment_complete'):
            return "care_planning"
    elif stage == 'care_planning':
        # Process care planning
        state = care_planner(state)
        # Could add condition here for returning to intake if needed
    
    return stage

# Agent 1: Intake Coordinator
def intake_coordinator(state: Dict) -> Dict:
    patient_data = state.get('patient_data', {})
    
    # Only process if not already completed
    if not patient_data.get('intake_complete'):
        system_prompt = """You are a medical intake coordinator with expertise in initial patient risk assessment.
        Provide a clear, structured assessment focusing ONLY on:
        1. Initial risk level (Low/Medium/High)
        2. Immediate concerns identified
        3. Recommended next steps
        4. Additional information needed

        Use bullet points and clear formatting. Do not include any 'thinking' process or metadata.
        """
        
        prompt = f"""
        Patient Information:
        {json.dumps(patient_data, indent=2)}
        
        Please provide your assessment in this EXACT format:

        ## Initial Risk Assessment

        **Risk Level:** [Low/Medium/High]

        **Immediate Concerns:**
        * [List concerns with bullet points]

        **Recommended Next Steps:**
        * [List steps with bullet points]

        **Additional Information Needed:**
        * [List needed information with bullet points]
        """
        
        response = llm.generate_response(prompt, system_prompt)
        
        # Update patient data with intake results
        if isinstance(response, dict) and 'content' in response:
            patient_data.update({
                "risk_assessment": response['content'],
                "intake_complete": True
            })
        else:
            patient_data.update({
                "risk_assessment": response,
                "intake_complete": True
            })
        
        state['patient_data'] = patient_data
    
    state['stage'] = 'intake'
    return state

# Agent 2: Clinical Assessment
def clinical_assessment(state: Dict) -> Dict:
    patient_data = state.get('patient_data', {})
    
    # Only process if not already completed
    if not patient_data.get('assessment_complete'):
        system_prompt = """You are a clinical assessment specialist.
        Provide a structured assessment following the format below EXACTLY.
        Use clear headers, numbered points, and bullet lists as specified.
        Do NOT include any metadata, thinking process, or tags in your response.
        """
        
        prompt = f"""
        Review this patient's information and provide a detailed clinical assessment:
        
        Patient Information:
        {json.dumps(patient_data, indent=2)}
        
        Format your response EXACTLY as follows:

        # Clinical Assessment

        ## 1. Detailed Symptom Analysis:

        * [Symptom 1 with details]
        * [Symptom 2 with details]
        * [Additional symptoms as needed]

        ## 2. Risk Level Determination: [Low/Medium/High] Risk

        * [Risk factor 1]
        * [Risk factor 2]
        * [Additional risk factors as needed]

        ## 3. Recommended Additional Screenings or Tests:

        1. [Test 1]
        2. [Test 2]
        3. [Additional tests as needed]

        ## 4. Potential Diagnoses to Consider:

        1. [Diagnosis 1]
        2. [Diagnosis 2]
        3. [Additional diagnoses as needed]

        ## 5. Areas Requiring Immediate Medical Attention:

        * [Area 1]
        * [Area 2]
        * [Additional areas as needed]
        """
        
        response = llm.generate_response(prompt, system_prompt)
        
        # Update patient data with clinical assessment
        if isinstance(response, dict) and 'content' in response:
            patient_data.update({
                "clinical_assessment": response['content'],
                "assessment_complete": True
            })
        else:
            patient_data.update({
                "clinical_assessment": response,
                "assessment_complete": True
            })
        
        state['patient_data'] = patient_data
    
    state['stage'] = 'assessment'
    return state

# Agent 3: Care Planner & Compliance
def care_planner(state: Dict) -> Dict:
    patient_data = state.get('patient_data', {})
    
    # Only process if not already completed
    if not patient_data.get('care_plan_complete'):
        system_prompt = """You are a care planning specialist.
        Provide detailed treatment recommendations following the format below EXACTLY.
        Use clear headers, numbered points, and bullet lists as specified.
        Do NOT include any metadata, thinking process, or tags in your response.
        """
        
        prompt = f"""
        Based on the patient's information and assessments, provide comprehensive treatment recommendations:
        
        Patient Information and Assessments:
        {json.dumps(patient_data, indent=2)}
        
        Format your response EXACTLY as follows:

        # Treatment Recommendations

        ## 1. Detailed Treatment Plan:

        * [Treatment component 1]
        * [Treatment component 2]
        * [Additional components as needed]

        ## 2. Care Level Determination:

        * [Routine/Urgent/Emergency]: [Brief justification]

        ## 3. Medication Recommendations:

        * [Medication 1 with dosage if applicable]
        * [Medication 2 with dosage if applicable]
        * [Additional medications as needed]

        ## 4. Lifestyle Modifications Needed:

        * [Modification 1]
        * [Modification 2]
        * [Additional modifications as needed]

        ## 5. Follow-up Schedule:

        * [Timeframe and type of follow-up]

        ## 6. Compliance Requirements:

        * [Requirement 1]
        * [Requirement 2]
        * [Additional requirements as needed]

        ## 7. Warning Signs to Watch For:

        * [Warning sign 1]
        * [Warning sign 2]
        * [Additional warning signs as needed]
        """
        
        response = llm.generate_response(prompt, system_prompt)
        
        # Extract care level from response
        care_level = "Routine"  # Default
        content = ""
        
        if isinstance(response, dict) and 'content' in response:
            content = response['content']
        else:
            content = response
            
        if "emergency" in content.lower():
            care_level = "Emergency"
        elif "urgent" in content.lower():
            care_level = "Urgent"
        
        # Update patient data with care plan
        patient_data.update({
            "treatment_recommendations": content,
            "care_level": care_level,
            "care_plan_complete": True
        })
        
        state['patient_data'] = patient_data
    
    state['stage'] = 'care_planning'
    return state

def create_agent_workflow() -> tuple[Graph, Dict]:
    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("intake", intake_coordinator)
    workflow.add_node("assessment", clinical_assessment)
    workflow.add_node("care_planning", care_planner)
    
    # Add edges
    workflow.add_edge("intake", "assessment")
    workflow.add_edge("assessment", "care_planning")
    workflow.add_edge("care_planning", "intake")

    # Store conditions in a separate dictionary
    conditions = {
        ("intake", "assessment"): lambda state: state['patient_data'].get('intake_complete', False),
        ("assessment", "care_planning"): lambda state: state['patient_data'].get('assessment_complete', False),
        ("care_planning", "intake"): lambda state: state['patient_data'].get('care_plan_complete', False)
    }

    # Set entry point
    workflow.set_entry_point("intake")
    
    # Return both workflow and conditions
    return workflow, conditions

def evaluate_condition(current_state: Dict, from_node: str, to_node: str, conditions: Dict) -> bool:
    """Check the transition condition for the given edge."""
    condition = conditions.get((from_node, to_node))
    if condition:
        return condition(current_state)
    return False

def transition(workflow: StateGraph, state: Dict, conditions: Dict) -> Dict:
    """Evaluate conditions and transition the state through the workflow."""
    from_stage = state['stage']
    
    # First process the current stage
    if from_stage == "intake":
        state = intake_coordinator(state)
    elif from_stage == "assessment":
        state = clinical_assessment(state)
    elif from_stage == "care_planning":
        state = care_planner(state)
        
    # Then determine the next stage
    next_stage = route(state)
    
    # Only try to transition if we're moving to a different stage
    if next_stage != from_stage:
        # Check if the condition for the transition is met
        if evaluate_condition(state, from_stage, next_stage, conditions):
            state['stage'] = next_stage
        else:
            raise ValueError(f"Transition from {from_stage} to {next_stage} is not allowed by the condition.")
    
    return state