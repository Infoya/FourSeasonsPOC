import os
import json
import requests
import openai
import warnings
import time
from dotenv import load_dotenv
import bs4
from bs4 import BeautifulSoup
import re
import urllib.parse

# Suppress Deprecation Warnings for now
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

if not openai.api_key or not ASSISTANT_ID:
    raise EnvironmentError("❌ Missing OPENAI_API_KEY or ASSISTANT_ID in your .env file")

# Global state
property_lookup = {}
selected_property = None
current_mode = None
booking_settings = {}
booking_flow = {}
result_set_id = None

# =============================
# Four Seasons API Wrappers
# =============================
def confirm_booking_if_available(start_date, end_date, destination):
    ows_code = "BLR546"
    print(f"🔍 Checking availability for {destination} ({ows_code}) from {start_date} to {end_date}")
    is_available = check_availability(ows_code)
    if not is_available:
        return f"❌ No rooms available at {destination} from {start_date} to {end_date}."

    persons = 2
    room_type = "STD"
    price = 15000.0
    result = post_result_set(start_date, end_date, destination, persons, room_type, price)
    return f"✅ Booking confirmed and added to cart with ID {result['id']} for {destination} from {start_date} to {end_date}."

def post_result_set(start_date, end_date, property_name, persons, room_type, price):
    url = "http://127.0.0.1:8080/resultSet"
    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "destination": property_name,
        "persons": persons,
        "room_type": room_type,
        "price": price
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def post_addons(result_set_id, sku_id, price, details):
    url = "http://127.0.0.1:8080/addOns"
    payload = {
        "result_set_id": result_set_id,
        "sku_id": sku_id,
        "price": price,
        "product_details": details
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

def get_cart_result_set(result_set_id):
    url = f"http://127.0.0.1:8080/cart/{result_set_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def checkout_result_set(result_set_id):
    url = f"http://127.0.0.1:8080/checkout/{result_set_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_property_dining(owsCode):
    url = f"https://www.fourseasons.com/alt/apps/fshr/feeds/product/availability?language=en&owsCode={owsCode}&categoryId=dining&currencyCode=INR&sourceName=Web+-+Shopping&timestamp=29190705&version=4"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_property_experiences(owsCode):
    url = f"https://www.fourseasons.com/alt/apps/fshr/feeds/product/availability?language=en&owsCode={owsCode}&categoryId=experiences&currencyCode=INR&sourceName=Web+-+Shopping&timestamp=29190705&version=4"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def check_availability(start_date, end_date):
    owsCode = "BLR546"  # default
    print(f"Checking availability for OWS Code: {owsCode}, Start: {start_date}, End: {end_date}")
    url = f"https://reservations.fourseasons.com/tretail/calendar/availability?propertySelection=SINGLE&hotelCityCode={owsCode}"
    response = requests.get(url)
    response.raise_for_status()
    print(response.json())
    return {"status": "Available"}

def get_fourseasons_properties():
    url = "https://reservations.fourseasons.com/content/en/properties"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def global_settings():
    url = "https://reservations.fourseasons.com/content/en/globalsettings"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def bookingflow():
    url = "https://reservations.fourseasons.com/tretail/content/bookingflow"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_all_properties():
    data = get_fourseasons_properties()
    regions = data.get("regions", [])
    all_properties = []
    for region in regions:
        for property in region.get("properties", []):
            all_properties.append({
                "name": property["name"],
                "owsCode": property["owsCode"],
                "tripteaseAPIKey": property.get("tripteaseAPIKey"),
                "region": region["title"]
            })
    return all_properties

def run_assistant():
    print("Welcome to the FourSeasons Assistant Booking CLI")
    try:
        global_settings()
        bookingflow()
        print("✅ Booking metadata loaded.")
    except Exception as e:
        print(f"❌ Failed to load booking metadata: {e}")
        return

    try:
        thread = openai.beta.threads.create()
        print("Thread created: ", thread.id)
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Thank you for using the Four Seasons assistant. Goodbye!")
            break

        try:
            openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input
            )
            print("Message sent to assistant")

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID
            )
            print("Assistant run started: ", run.id)

            while True:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                print("Run status:", run_status.status)

                if run_status.status == "completed":
                    break
                elif run_status.status == "requires_action":
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = []

                    for call in tool_calls:
                        name = call.function.name
                        args = json.loads(call.function.arguments)
                        print(f"🔧 Calling tool: {name} with arguments: {args}")

                        try:
                            if name == "check_availability":
                                result = check_availability(
                                    start_date=args["start_date"],
                                    end_date=args["end_date"]
                                )
                                tool_outputs.append({
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result)
                                })

                            elif name == "get_fourseasons_properties":
                                result = get_fourseasons_properties()
                                tool_outputs.append({
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result)
                                })

                            elif name == "confirm_booking_if_available":
                                result = confirm_booking_if_available(
                                    start_date=args["start_date"],
                                    end_date=args["end_date"],
                                    destination=args["destination"]
                                )
                                tool_outputs.append({
                                    "tool_call_id": call.id,
                                    "output": result
                                })
                        except Exception as e:
                            print(f"❌ Tool {name} failed: {e}")

                    openai.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ["failed", "cancelled"]:
                    print(f"❌ Run failed with status: {run_status.status}")
                    break

                time.sleep(1)

            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            for msg in reversed(messages.data):
                if msg.role == "assistant":
                    print(f"\nAI: {msg.content[0].text.value}")
                    break
        except Exception as e:
            print(f"❌ Error during assistant interaction: {e}")

if __name__ == "__main__":
    run_assistant()


# =============================
# Utils and Flows
# =============================
# def is_booking_related(user_input):
#     keywords = ["book", "booking", "check availability", "property", "room", "hotel", "reserve", "stay"]
#     return any(kw in user_input.lower() for kw in keywords)
#
# def browse_properties_flow():
#     global selected_property, result_set_id
#     print("\nSelect any available property:")
#     properties = fetch_all_properties()
#     property_lookup = {str(i+1): prop for i, prop in enumerate(properties)}
#     for idx, prop in property_lookup.items():
#         print(f"{idx}. {prop['name']} ({prop['owsCode']}) - {prop['region']}")
#
#     selected_index = input("\nEnter the number of the property you want to check: ").strip()
#     selected_property = property_lookup.get(selected_index)
#
#     if not selected_property:
#         print("Invalid selection. Try again.\n")
#         return
#
#     print(f"\nSelected: {selected_property['name']}")
#     try:
#         is_available = check_availability(selected_property['owsCode'])
#         if not is_available:
#             print("\nPlease select a different property.\n")
#             return
#     except requests.HTTPError as e:
#         print(f"\nCould not check availability: {e}")
#         return
#
#     decision = input("\nDo you want to add this property to cart? (yes/no): ").strip().lower()
#     if decision != "yes":
#         print("You can restart to explore other properties.")
#         return
#
#     start_date = input("Enter check-in date (YYYY-MM-DD): ").strip()
#     end_date = input("Enter check-out date (YYYY-MM-DD): ").strip()
#     persons = int(input("Enter number of persons: ").strip())
#     room_type = input("Enter room type code: ").strip()
#     price = 10000.0
#
#     result = post_result_set(start_date, end_date, selected_property['name'], persons, room_type, price)
#     result_set_id = result["id"]
#     print(f"Added to cart with result_set_id = {result_set_id}")
#
#     dining = get_property_dining(selected_property['owsCode'])
#     experiences = get_property_experiences(selected_property['owsCode'])
#
#     dining_addons = []
#     experience_addons = []
#
#     print("\nAvailable Dining Addons:")
#     for category in dining.get("categories", []):
#         for item in category.get("products", []):
#             for price in item.get('prices', []):
#                 idx = len(dining_addons) + 1
#                 addon_code = f"D{idx}"
#                 print(f"{addon_code}. {item['name']}\n{item['description']}\n{price.get('subtitle', '')} - ₹{price.get('amount', '')} ({price.get('type', '')})\n")
#                 dining_addons.append({"code": addon_code, "name": item["name"], "sku": item["sku"], "amount": price.get("amount")})
#
#     print("\nAvailable Local Experiences Addons:")
#     for category in experiences.get("categories", []):
#         for item in category.get("products", []):
#             for price in item.get('prices', []):
#                 idx = len(experience_addons) + 1
#                 addon_code = f"L{idx}"
#                 print(f"{addon_code}. {item['name']}\n{item['description']}\n{price.get('subtitle', '')} - ₹{price.get('amount', '')} ({price.get('type', '')})\n")
#                 experience_addons.append({"code": addon_code, "name": item["name"], "sku": item["sku"], "amount": price.get("amount")})
#
#     while True:
#         addon_choice = input("\nEnter Addon code to add (e.g. D1, L2) or 'done' to continue: ").strip().upper()
#         if addon_choice == "DONE":
#             break
#         found = False
#         for addon in dining_addons + experience_addons:
#             if addon["code"] == addon_choice:
#                 post_addons(result_set_id, addon["sku"], addon["amount"], addon["name"])
#                 print(f"✅ Added addon: {addon['name']}")
#                 found = True
#                 break
#         if not found:
#             print("❌ Invalid addon code.")
#
#     next_step = input("\nDo you want to go to checkout? (yes/no): ").strip().lower()
#     if next_step != "yes":
#         print("You can continue shopping later. Goodbye!")
#         return
#
#     cart = get_cart_result_set(result_set_id)
#     print("\nCart Summary:")
#     print(json.dumps(cart, indent=2))
#
#     checkout = checkout_result_set(result_set_id)
#     print("\nTo complete your booking, visit this payment URL:")
#     print(checkout.get("checkout_url", "[Payment link unavailable]"))
#
# # =============================
# # Web Search using OpenAI Tool
# # =============================
# def web_search(query):
#     print("\n🔎 Using OpenAI web-search tool to answer your query...\n")
#     try:
#         thread = openai.beta.threads.create()
#         thread_id = thread.id
#
#         openai.beta.threads.messages.create(
#             thread_id=thread_id,
#             role="user",
#             content=query
#         )
#
#         run = openai.beta.threads.runs.create(
#             thread_id=thread_id,
#             assistant_id=ASSISTANT_ID,
#             tools=[{"type": "web-search"}]
#         )
#
#         while True:
#             run_status = openai.beta.threads.runs.retrieve(
#                 thread_id=thread_id,
#                 run_id=run.id
#             )
#             if run_status.status == "completed":
#                 break
#             elif run_status.status in ["failed", "cancelled"]:
#                 print(f"❌ Web search failed with status: {run_status.status}")
#                 return
#             time.sleep(1)
#
#         messages = openai.beta.threads.messages.list(thread_id=thread_id)
#         for msg in reversed(messages.data):
#             if msg.role == "assistant":
#                 print(f"\n🤖 {msg.content[0].text.value}")
#                 break
#
#     except Exception as e:
#         print(f"\n❌ Failed to perform advanced web search: {e}")

# =============================
# Main
# =============================
# if __name__ == "__main__":
#     print("Welcome to the FourSeasons Assistant Booking CLI")
#     print("Loading booking metadata...\n")
#     booking_settings = global_settings()
#     booking_flow = bookingflow()
#     print("✅ Booking metadata loaded.\n")
#     print("\nHi! I'm your Four Seasons assistant. How can I help you today?\n(Type 'exit' or 'quit' to leave)\n>")
#
#     while True:
#         user_input = input("You :").strip()
#
#         if user_input.lower() in ["exit", "quit"]:
#             print("Thank you for using the Four Seasons assistant. Goodbye!")
#             break
#
#         if is_booking_related(user_input):
#             browse_properties_flow()
#         else:
#             web_search("Four Seasons " + user_input)

