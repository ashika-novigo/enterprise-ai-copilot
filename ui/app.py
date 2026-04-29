# ui/app.py
import gradio as gr
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
 
from graph.workflow import run_copilot
from db.database import init_db
 
# Initialize SQLite tables on startup
init_db()
 
# ── State ─────────────────────────────────────────
# Gradio stores per-session state in gr.State()
 
def chat_response(message, history, employee_id, user_role, user_email):
    """Called every time user sends a message."""
    if not message.strip():
        return history, ''
    

    if history is None:
        history = []


 
    # Gradio Chatbot expects a list of message dicts in OpenAI format
    history.append({
        "role": "user",
        "content": message
    })
    
    # Call the LangGraph copilot
    response = run_copilot(
        query=message,
        employee_id=int(employee_id),
        user_role=user_role,
        user_email=user_email,
        thread_id=f'user_{employee_id}',
    )
    
    # Ensure we have a response
    if not response:
        response = "⚠️ No response generated. Please try again."
    
    history.append({
        "role": "assistant",
        "content": response
    })
    return history, ''
 

 
def clear_chat():
    return [], ''
 
# ── Build the Gradio UI ───────────────────────────
with gr.Blocks(title='Enterprise AI Copilot') as app:
 
    gr.Markdown('# 🤖 Enterprise Multi-Agent AI Copilot')
    gr.Markdown('Powered by **Google Gemini** | LangGraph | SQLite | ChromaDB')
 
    with gr.Row():
        # Left sidebar: user login
        with gr.Column(scale=1):
            gr.Markdown('### 👤 Login')
            employee_id = gr.Number(label='Employee ID', value=1, precision=0)
            user_name   = gr.Textbox(label='Name', value='John Doe')
            user_email  = gr.Textbox(label='Email', value='john@company.com')
            user_role   = gr.Dropdown(
                label='Role',
                choices=['employee','manager','hr','it','finance','admin'],
                value='employee'
            )
            department = gr.Dropdown(
                label='Department',
                choices=['Engineering','HR','IT','Finance','Sales'],
                value='Engineering'
            )
            gr.Markdown('---')
            gr.Markdown('**Quick Examples:**')
            gr.Markdown('- What is the WFH policy?')
            gr.Markdown('- Apply leave for 2025-08-04 to 2025-08-06')
            gr.Markdown('- My VPN is not working')
            gr.Markdown('- Check my leave balance')
 
        # Right area: chat
        with gr.Column(scale=3):
            chatbot  = gr.Chatbot(label='Copilot', height=500)
            msg_box  = gr.Textbox(
                label='Your message',
                placeholder='Ask about HR, IT support, or Finance...',
                lines=2
            )
            with gr.Row():
                send_btn  = gr.Button('Send', variant='primary')
                clear_btn = gr.Button('Clear Chat')
 
    # ── Wire up events ────────────────────────────
    send_btn.click(
        fn=chat_response,
        inputs=[msg_box, chatbot, employee_id, user_role, user_email],
        outputs=[chatbot, msg_box]
    )
    msg_box.submit(  # also send on Enter key
        fn=chat_response,
        inputs=[msg_box, chatbot, employee_id, user_role, user_email],
        outputs=[chatbot, msg_box]
    )
    clear_btn.click(fn=clear_chat, outputs=[chatbot, msg_box])
 
if __name__ == '__main__':
    app.launch(
        server_name='127.0.0.1',   # localhost only
        server_port=7860,
        share=False,               # set True to get public URL
        inbrowser=True,            # auto-opens browser on Windows
        theme=gr.themes.Soft()
    )
