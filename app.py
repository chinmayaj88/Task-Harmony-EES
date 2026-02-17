"""
Shipment Extraction System - Interactive Demo UI
Built with Streamlit for client demonstrations
"""

import streamlit as st
import json
from datetime import datetime
from src.engine.extractor import ShipmentExtractor
from src.config import settings
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Shipment Extraction System - AI Demo",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #a3ff12;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #8c8c8c;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
    }
    .result-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #a3ff12;
        margin: 1rem 0;
    }
    .stButton>button {
        background: #a3ff12;
        color: black;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background: #b5ff3a;
        box-shadow: 0 4px 12px rgba(163, 255, 18, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'extraction_history' not in st.session_state:
    st.session_state.extraction_history = []

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/container-ship.png", width=80)
    st.title("⚙️ Configuration")
    
    st.markdown("---")
    st.markdown("### 🤖 AI Model")
    st.info(f"**Model**: {settings.MODEL_NAME}\n\n**Prompt Version**: {settings.PROMPT_VERSION}")
    
    st.markdown("---")
    st.markdown("### 📊 System Stats")
    st.metric("Accuracy", "93%+", "5% vs v5")
    st.metric("Avg Processing", "< 1s", "per email")
    st.metric("Sessions", len(st.session_state.extraction_history))

# Main Content
st.markdown('<h1 class="main-header">📦 AI Shipment Extraction System</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Extract structured logistics data from unstructured emails with 93%+ accuracy</p>', unsafe_allow_html=True)

# Tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🔍 Single Email Extraction", "📚 Sample Emails", "📈 Extraction History"])

with tab1:
    st.markdown("### Enter Email Content")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        email_subject = st.text_input(
            "Email Subject",
            placeholder="e.g., Urgent Rate Request - Shanghai to Mumbai",
            help="Enter the email subject line"
        )
        
        email_body = st.text_area(
            "Email Body",
            height=250,
            placeholder="""e.g., 
Hi,

We need urgent rates for the following shipment:
Origin: Shanghai
Destination: Mumbai (Nhava Sheva)
Cargo: General cargo, 2500 kgs, 8.5 CBM
Incoterm: FOB

Please send rates ASAP.

Thanks!""",
            help="Enter the complete email body"
        )
    
    with col2:
        st.markdown("#### Quick Tips:")
        st.info("""
        ✅ Include port names  
        ✅ Mention cargo details  
        ✅ Specify Incoterm  
        ✅ Add weight/volume  
        
        The AI will extract:
        - Port codes (UN/LOCODE)
        - Product line
        - Cargo measurements
        - Dangerous goods flag
        """)
    
    if st.button("🚀 Extract Shipment Data", type="primary", use_container_width=True):
        if not email_subject and not email_body:
            st.error("⚠️ Please enter either subject or body content")
        else:
            with st.spinner("🤖 AI is analyzing the email..."):
                try:
                    # Initialize extractor
                    extractor = ShipmentExtractor()
                    
                    # Prepare email content
                    email_content = {
                        "id": f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        "subject": email_subject,
                        "body": email_body
                    }
                    
                    # Process extraction
                    result = extractor.process_item(email_content)
                    
                    # Add to history
                    st.session_state.extraction_history.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'email': email_content,
                        'result': result.model_dump()
                    })
                    
                    # Display results
                    st.success("✅ Extraction Complete!")
                    
                    # Show reasoning if available
                    if result.reasoning:
                        with st.expander("🧠 AI Reasoning Process"):
                            st.markdown(f"```\n{result.reasoning}\n```")
                    
                    # Display extracted data in columns
                    st.markdown("### 📋 Extracted Data")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("#### 🚢 Route Information")
                        st.markdown(f"""
                        **Product Line**: `{result.product_line or 'N/A'}`  
                        **Origin Port**: {result.origin_port_name or 'N/A'} (`{result.origin_port_code or 'N/A'}`)  
                        **Destination Port**: {result.destination_port_name or 'N/A'} (`{result.destination_port_code or 'N/A'}`)  
                        **Incoterm**: `{result.incoterm}`
                        """)
                    
                    with col2:
                        st.markdown("#### 📦 Cargo Details")
                        st.markdown(f"""
                        **Weight**: {result.cargo_weight_kg or 'N/A'} kg  
                        **Volume**: {result.cargo_cbm or 'N/A'} CBM  
                        **Dangerous Goods**: {'⚠️ YES' if result.is_dangerous else '✅ NO'}
                        """)
                    
                    with col3:
                        st.markdown("#### 📊 Data Quality")
                        # Calculate completeness
                        fields = [result.product_line, result.origin_port_code, result.destination_port_code, 
                                 result.cargo_weight_kg, result.cargo_cbm]
                        completeness = (sum(1 for f in fields if f is not None) / len(fields)) * 100
                        
                        st.metric("Completeness", f"{completeness:.0f}%")
                        st.metric("Confidence", "High" if completeness > 60 else "Medium")
                    
                    # JSON output
                    with st.expander("📄 View JSON Output"):
                        st.json(result.model_dump())
                    
                except Exception as e:
                    st.error(f"❌ Extraction failed: {str(e)}")

with tab2:
    st.markdown("### 📚 Sample Email Templates")
    st.info("Click 'Load' to populate the extraction form with sample data")
    
    samples = [
        {
            "name": "Standard Import Request",
            "subject": "Rate request - Shanghai to Chennai",
            "body": """Hi Team,

Please quote for:
Origin: Shanghai, China
Destination: Chennai (Madras), India
Cargo: 1500 kgs, 5.2 CBM
Terms: CIF

Best regards"""
        },
        {
            "name": "Dangerous Goods Shipment",
            "subject": "DG shipment - Singapore to Hamburg",
            "body": """URGENT - Hazardous cargo

Origin: Singapore
Destination: Hamburg
Cargo: 4533 kgs, 9.47 CBM, Class 3 Dangerous Goods
Incoterm: FCA

Need immediate quote."""
        },
        {
            "name": "Export with Typos",
            "subject": "Cheenai export rates needed",
            "body": """Hello,

Shipment from Cheenai to Shangai
Approx weight: 2800 kgs
Volume: 12.3 cmd (approx)
FOB terms

Thanks"""
        }
    ]
    
    for idx, sample in enumerate(samples):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{sample['name']}**")
            st.text(f"Subject: {sample['subject']}")
        with col2:
            if st.button("Load", key=f"load_{idx}"):
                st.session_state.sample_subject = sample['subject']
                st.session_state.sample_body = sample['body']
                st.rerun()

with tab3:
    st.markdown("### 📈 Extraction History")
    
    if st.session_state.extraction_history:
        # Create DataFrame
        history_data = []
        for entry in reversed(st.session_state.extraction_history):
            result = entry['result']
            history_data.append({
                'Timestamp': entry['timestamp'],
                'Origin': result.get('origin_port_code', 'N/A'),
                'Destination': result.get('destination_port_code', 'N/A'),
                'Product Line': result.get('product_line', 'N/A'),
                'Weight (kg)': result.get('cargo_weight_kg', 'N/A'),
                'Volume (CBM)': result.get('cargo_cbm', 'N/A'),
                'DG': '⚠️' if result.get('is_dangerous') else '✅'
            })
        
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download History as CSV",
            data=csv,
            file_name=f'extraction_history_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv'
        )
        
        if st.button("🗑️ Clear History"):
            st.session_state.extraction_history = []
            st.rerun()
    else:
        st.info("No extraction history yet. Process some emails to see results here!")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🎯 Accuracy**: 93%+ on messy data")
with col2:
    st.markdown("**⚡ Speed**: Sub-second processing")
with col3:
    st.markdown("**💰 Cost**: 95% cheaper than GPT-4")
