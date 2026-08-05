from openai import OpenAI
from dotenv import load_dotenv
import os
from ai.decision import analyze_call
from app.order import order

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt = f"""
You are ConfirmAI.

You are calling this customer:

Name: {order['customer_name']}
Product: {order['product']}
Price: {order['price']} DH
City: {order['city']}
Address: {order['address']}

Start the conversation exactly like a professional Moroccan e-commerce agent.

Ask if the customer confirms the order.
"""

response = client.responses.create(
    model="gpt-5",
    input=prompt
)

print("\n" + "=" * 50)
print("📞 CONFIRMAI")
print("=" * 50)

print(f"👤 Customer : {order['customer_name']}")
print(f"🛍️ Product  : {order['product']}")
print(f"💰 Price    : {order['price']} DH")
print(f"📍 City     : {order['city']}")

print("=" * 50)
print("🤖 AI RESPONSE")
print("=" * 50)

print(response.output_text)

print("=" * 50)
print(response.output_text)
result = analyze_call(response.output_text)

print("\n" + "=" * 50)
print("📊 CALL ANALYSIS")
print("=" * 50)


