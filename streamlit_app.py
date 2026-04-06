import streamlit as st
import json
import os
from dotenv import load_dotenv
from main import get_supper_summary, get_top_news_with_content, SERP_API_KEY, GROQ_API_KEY, get_refined_suggestions

# Load environment variables
load_dotenv()

# Initialize session state
if 'main_search' not in st.session_state:
    st.session_state.main_search = ""
if 'trigger_search' not in st.session_state:
    st.session_state.trigger_search = False

# Page configuration
st.set_page_config(
    page_title="Diggi News Analysis",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for a premium look
st.markdown("""
    <style>
    .main {
        background-color: black;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .article-card {
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: white;
        transition: transform 0.2s;
    }
    .article-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .suggestion-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Function to handle search trigger
def start_search(q):
    st.session_state.query_input = q
    st.session_state.trigger_search = True

# Sidebar
with st.sidebar:
# ... (existing sidebar code)
    st.title("⚙️ Configuration")
    api_key_serp = st.text_input("SerpApi Key", value=SERP_API_KEY, type="password")
    api_key_groq = st.text_input("Groq API Key", value=GROQ_API_KEY, type="password")
    
    st.divider()
    num_results = st.slider("Number of articles to fetch", 1, 10, 3)
    
    st.info("Analysis is powered by Diggi framework and Llama-3-70B.")

# Main content
st.title("📰 Diggi News Analysis")
st.markdown("Enter a topic to get a structured, multi-source analytical report.")

# Input field bonded to session state
query = st.text_input("Search for a news topic...", placeholder="e.g., SpaceX Starship launch, AI regulation in EU", key="main_search")

# Check if search was triggered by "Use it" button
if st.session_state.trigger_search:
    st.session_state.trigger_search = False
    run_analysis = True
else:
    run_analysis = st.button("🔍 Analyze News")

if run_analysis:
    if not query:
        st.warning("Please enter a search query.")
    elif not api_key_serp or not api_key_groq:
        st.error("Please provide both SerpApi and Groq API keys in the sidebar.")
    else:
        # Check if query is vague
        words = query.strip().split()
        if len(words) < 3:
            st.warning(f"⚠️ **'{query}'** is quite vague. For better results, try a more specific news topic.")
            st.write("### 💡 Recommended Searches")
            
            with st.spinner("Generating better search queries..."):
                suggestions = get_refined_suggestions(query)
                
            if suggestions:
                for suggestion in suggestions:
                    col_text, col_btn = st.columns([0.8, 0.2])
                    with col_text:
                        st.info(suggestion)
                    with col_btn:
                        if st.button("Use it", key=f"use_{suggestion}"):
                            st.session_state.main_search = suggestion
                            st.session_state.trigger_search = True
                            st.rerun()
            else:
                st.error("Could not generate suggestions. Please try a more detailed query.")
        else:
            with st.status("Fetching and analyzing news...", expanded=True) as status:
                st.write("Step 1: Searching for articles...")
                # We can use the imported functions directly
                articles = get_top_news_with_content(query, serp_api_key=api_key_serp, num_results=num_results)
                
                if not articles:
                    st.error("No relevant news articles found.")
                    status.update(label="Analysis failed.", state="error")
                else:
                    st.write(f"Step 2: Analyzing {len(articles)} articles...")
                    analysis = get_supper_summary(query, serp_api_key=api_key_serp, num_results=num_results)
                    
                    if not analysis:
                        st.error("Failed to generate analytical report.")
                        status.update(label="Analysis failed.", state="error")
                    else:
                        status.update(label="Analysis complete!", state="complete", expanded=False)
                        st.session_state.articles = articles
                        st.session_state.analysis = analysis

# Check if analysis results are in session state and display them
if 'analysis' in st.session_state and st.session_state.analysis:
    articles = st.session_state.articles
    analysis = st.session_state.analysis
    
    # Display original articles
    st.subheader("📌 Source Articles")
    cols = st.columns(len(articles))
    for i, article in enumerate(articles):
        with cols[i]:
            st.markdown(f"""
            <div class="article-card">
                <img src="{article['thumbnail']}" style="width:100%; border-radius:5px;">
                <h4>{article['title']}</h4>
                <p><strong>Source:</strong> {article['source']}</p>
                <a href="{article['link']}" target="_blank">Read Original</a>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Display Analytical Dimensions
    st.subheader("📊 Analytical Dimensions")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🎯 Claims", 
        "⚖️ Perspectives", 
        "🔍 Evidence", 
        "🛡️ Credibility", 
        "📜 History", 
        "❓ Questions"
    ])
    
    with tab1:
        st.write("### Claim-Level Focus")
        for claim in analysis.claim_level_focus.claims:
            with st.expander(f"**Claim:** {claim.claim}"):
                st.write(f"**Actors:** {', '.join(claim.actors)}")
                st.info(f"**Evidence:** {claim.evidence}")
                
    with tab2:
        st.write("### Perspectives & Disagreements")
        st.write("#### Consensus Points")
        for point in analysis.multi_source_comparison.consensus_points:
            st.success(f"✅ {point}")
            
        st.write("#### Disagreement Points")
        for point in analysis.multi_source_comparison.disagreement_points:
            st.warning(f"⚠️ {point}")
            
        st.write("#### Stakeholder Views")
        for p in analysis.perspectives.perspectives:
            st.write(f"**{p.stakeholder}:** {p.viewpoint}")
            st.caption(f"Reasoning: {p.reasoning}")

    with tab3:
        st.write("### Evidence Traceability")
        for trace in analysis.evidence_traceability.evidence:
            st.markdown(f"**Statement:** {trace.statement}")
            st.markdown(f"> *\"{trace.supporting_passage}\"*")
            st.caption(f"Source: [{trace.source}]({trace.link})")
            st.divider()

    with tab4:
        st.write("### Credibility Signals")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Source Reliability", analysis.credibility_signals.source_reliability)
        with col_b:
            st.metric("Confidence Level", analysis.credibility_signals.confidence_level)
            
        st.write("#### Verified Facts")
        for fact in analysis.credibility_signals.verified_facts:
            st.markdown(f"- {fact}")
            
        st.write("#### Uncertain Claims")
        for claim in analysis.credibility_signals.uncertain_claims:
            st.markdown(f"- ❓ {claim}")

    with tab5:
        st.write("### Historical & Situational Framing")
        st.info(analysis.historical_context.background)
        
        st.write("#### Timeline")
        for event in analysis.historical_context.timeline:
            st.markdown(f"- **{event.date}:** {event.event}")

    with tab6:
        st.write("### Exploratory Questions & Topics")
        st.write("#### Questions for Further Investigation")
        for q in analysis.exploratory_questions.questions:
            st.markdown(f"- {q}")
            
        st.write("#### Related Topics")
        st.write(", ".join(analysis.exploratory_questions.related_topics))

# Footer
st.divider()
st.caption("Built with Diggi News Analysis Framework • Streamlit • Groq • SerpApi")
