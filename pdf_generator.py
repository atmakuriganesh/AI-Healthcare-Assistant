from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import io
import re

class PDFGenerator:
    def __init__(self):
        # Initialize styles
        self.styles = getSampleStyleSheet()
        
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=24,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Section heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        # Subheading style
        self.subheading_style = ParagraphStyle(
            'CustomSubheading',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=4,
            spaceAfter=4,
            fontName='Helvetica'
        )
        
        # Bullet point style
        self.bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=20,
            bulletIndent=10,
            fontName='Helvetica'
        )
        
        # Label style for tables
        self.label_style = ParagraphStyle(
            'CustomLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold'
        )
        
        # Value style for tables
        self.value_style = ParagraphStyle(
            'CustomValue',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica'
        )
        
        # Care level style
        self.care_level_style = ParagraphStyle(
            'CareLevel',
            parent=self.styles['Heading2'],
            fontSize=14,
            alignment=TA_CENTER,
            spaceBefore=12,
            spaceAfter=12,
            textColor=colors.white,
            fontName='Helvetica-Bold'
        )
        
        # Disclaimer style
        self.disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.gray,
            fontName='Helvetica-Oblique'
        )
    
    def format_markdown_content(self, text):
        """Format markdown-like content for PDF rendering"""
        if not text:
            return []
            
        elements = []
        
        # Split by sections (using markdown headings)
        sections = re.split(r'(#+\s+.*)', text)
        
        current_heading_level = 0
        
        for section in sections:
            if not section.strip():
                continue
                
            # Check if this is a heading
            heading_match = re.match(r'(#+)\s+(.*)', section)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                
                # Choose style based on heading level
                if level == 1:
                    elements.append(Paragraph(heading_text, self.heading_style))
                    current_heading_level = 1
                elif level == 2:
                    elements.append(Paragraph(heading_text, self.subheading_style))
                    current_heading_level = 2
                else:
                    elements.append(Paragraph(heading_text, self.subheading_style))
                    current_heading_level = 3
            else:
                # Process content - split by lines for bullet points
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Check for bullet points
                    bullet_match = re.match(r'^\s*[\*\-]\s+(.*)', line)
                    if bullet_match:
                        bullet_text = bullet_match.group(1)
                        elements.append(Paragraph(f"• {bullet_text}", self.bullet_style))
                    # Check for numbered lists
                    numbered_match = re.match(r'^\s*(\d+)\.\s+(.*)', line)
                    if numbered_match:
                        number = numbered_match.group(1)
                        item_text = numbered_match.group(2)
                        elements.append(Paragraph(f"{number}. {item_text}", self.bullet_style))
                    # Regular paragraph
                    elif line and not bullet_match and not numbered_match:
                        # Check if it has bold or emphasized text
                        line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)  # Bold
                        line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)      # Italic
                        elements.append(Paragraph(line, self.normal_style))
        
        return elements
    
    def create_patient_info_table(self, patient_data):
        """Create a nicely formatted patient info table"""
        data = []
        
        # Add rows with label and value
        if 'name' in patient_data:
            data.append([Paragraph("Name:", self.label_style), 
                        Paragraph(patient_data['name'], self.value_style)])
        
        if 'contact' in patient_data:
            data.append([Paragraph("Contact:", self.label_style), 
                        Paragraph(patient_data['contact'], self.value_style)])
        
        if 'dob' in patient_data:
            data.append([Paragraph("Date of Birth:", self.label_style), 
                        Paragraph(patient_data['dob'], self.value_style)])
        
        if 'emergency_contact' in patient_data:
            data.append([Paragraph("Emergency Contact:", self.label_style), 
                        Paragraph(patient_data['emergency_contact'], self.value_style)])
        
        if 'emergency_relation' in patient_data:
            data.append([Paragraph("Relation:", self.label_style), 
                        Paragraph(patient_data['emergency_relation'], self.value_style)])
        
        if 'gender' in patient_data:
            data.append([Paragraph("Gender:", self.label_style), 
                        Paragraph(patient_data['gender'], self.value_style)])
        
        # Create the table
        table = Table(data, colWidths=[1.5*inch, 4.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def create_clinical_assessment_table(self, patient_data):
        """Create a table with clinical assessment metrics"""
        data = []
        
        # Add rows with clinical metrics
        if 'pain_level' in patient_data:
            data.append([Paragraph("Pain Level:", self.label_style), 
                        Paragraph(str(patient_data['pain_level']), self.value_style)])
        
        if 'duration' in patient_data:
            data.append([Paragraph("Duration:", self.label_style), 
                        Paragraph(patient_data['duration'], self.value_style)])
        
        if 'symptom_frequency' in patient_data:
            data.append([Paragraph("Frequency:", self.label_style), 
                        Paragraph(patient_data['symptom_frequency'], self.value_style)])
        
        if 'previous_treatment' in patient_data:
            data.append([Paragraph("Previous Treatment:", self.label_style), 
                        Paragraph(patient_data['previous_treatment'], self.value_style)])
        
        # Create the table if we have data
        if data:
            table = Table(data, colWidths=[1.5*inch, 4.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            return table
        
        return None
    
    def create_care_level_box(self, care_level):
        """Create a highlighted box showing care level"""
        # Define colors based on care level
        care_colors = {
            "Routine": colors.green,
            "Urgent": colors.orange,
            "Emergency": colors.red,
        }
        
        color = care_colors.get(care_level, colors.gray)
        
        data = [[Paragraph(f"Care Level: {care_level}", self.care_level_style)]]
        table = Table(data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
        ]))
        
        return table
    
    def create_medical_report(self, patient_data):
        """Create a well-formatted medical report PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )
        
        # Build the story (content)
        story = []
        
        # Title
        story.append(Paragraph("Medical Assessment Report", self.title_style))
        
        # Date and Time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Report Generated: {current_time}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # Patient Information Section
        story.append(Paragraph("Patient Information", self.heading_style))
        patient_table = self.create_patient_info_table(patient_data)
        story.append(patient_table)
        story.append(Spacer(1, 15))
        
        # Primary Complaints
        story.append(Paragraph("Primary Complaints", self.heading_style))
        if 'primary_complaints' in patient_data:
            story.append(Paragraph(patient_data.get('primary_complaints', 'None reported'), self.normal_style))
        story.append(Spacer(1, 15))
        
        # Risk Assessment
        story.append(Paragraph("Initial Risk Assessment", self.heading_style))
        if 'risk_assessment' in patient_data:
            risk_elements = self.format_markdown_content(patient_data['risk_assessment'])
            story.extend(risk_elements)
        else:
            story.append(Paragraph("No risk assessment available", self.normal_style))
        story.append(Spacer(1, 15))
        
        # Clinical Assessment
        story.append(Paragraph("Clinical Assessment", self.heading_style))
        clinical_table = self.create_clinical_assessment_table(patient_data)
        if clinical_table:
            story.append(clinical_table)
            story.append(Spacer(1, 10))
            
        if 'clinical_assessment' in patient_data:
            story.append(Paragraph("Detailed Assessment:", self.subheading_style))
            clinical_elements = self.format_markdown_content(patient_data['clinical_assessment'])
            story.extend(clinical_elements)
        else:
            story.append(Paragraph("No detailed assessment available", self.normal_style))
        
        # Check if we need a page break
        story.append(PageBreak())
        
        # Treatment Recommendations
        story.append(Paragraph("Treatment Recommendations", self.heading_style))
        if 'treatment_recommendations' in patient_data:
            treatment_elements = self.format_markdown_content(patient_data['treatment_recommendations'])
            story.extend(treatment_elements)
        else:
            story.append(Paragraph("No treatment recommendations available", self.normal_style))
        story.append(Spacer(1, 15))
        
        # Care Level
        if 'care_level' in patient_data:
            story.append(Paragraph("Care Level Determination", self.heading_style))
            care_level_box = self.create_care_level_box(patient_data['care_level'])
            story.append(care_level_box)
            story.append(Spacer(1, 20))
        
        # Disclaimer
        story.append(Spacer(1, 20))
        story.append(Paragraph("Disclaimer", self.heading_style))
        disclaimer_text = """This report was generated by the Healthcare Navigator AI system. It is intended for informational 
        purposes only and should be reviewed by a qualified healthcare professional. This is not a substitute for 
        professional medical advice, diagnosis, or treatment."""
        story.append(Paragraph(disclaimer_text, self.disclaimer_style))
        
        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return buffer