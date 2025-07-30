import os
import json
import requests
import openai
import warnings
import time
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date

# Suppress Deprecation Warnings for now
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

if not openai.api_key or not ASSISTANT_ID:
    raise EnvironmentError(
        "❌ Missing OPENAI_API_KEY or ASSISTANT_ID in your .env file"
    )

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
    persons = 2
    room_type = "STD"
    price = 15000.0
    result = post_result_set(
        start_date, end_date, destination, persons, room_type, price
    )
    return {
        "status": "success",
        "message": f"Booking confirmed for {destination} from {start_date} to {end_date}.",
        "next_action": "ask_addons",
        "result_set_id": result["id"],
        "destination": destination,
    }


def post_result_set(start_date, end_date, property_name, persons, room_type, price):
    url = "http://127.0.0.1:8000/resultSet"
    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "destination": property_name,
        "persons": persons,
        "room_type": room_type,
        "price": price,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print(response.json())
    return response.json()


def post_addons(result_set_id, sku_id, price, details):
    url = "http://127.0.0.1:8000/addOns"
    payload = {
        "result_set_id": result_set_id,
        "sku_id": sku_id,
        "price": price,
        "product_details": details,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_cart_result_set(result_set_id):
    url = f"http://127.0.0.1:8000/cart/{result_set_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def checkout_result_set(result_set_id):
    url = f"http://127.0.0.1:8000/checkout/{result_set_id}"
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


def check_availability(owsCode, start_date, end_date):
    url = f"https://reservations.fourseasons.com/tretail/calendar/availability?propertySelection=SINGLE&hotelCityCode={owsCode}"
    response = requests.get(url)
    response.raise_for_status()
    return {
        "status": "available",
        "owsCode": owsCode,
        "start_date": start_date,
        "end_date": end_date,
        "message": f"✅ The property with OWS Code {owsCode} is available from {start_date} to {end_date}.",
        "next_action": "prompt_confirm_booking",
    }


def get_fourseasons_properties():
    url = "https://reservations.fourseasons.com/content/en/properties"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# def global_settings():
#     url = "https://reservations.fourseasons.com/content/en/globalsettings"
#     response = requests.get(url)
#     response.raise_for_status()
#     return response.json()
#
# def bookingflow():
#     url = "https://reservations.fourseasons.com/tretail/content/bookingflow"
#     response = requests.get(url)
#     response.raise_for_status()
#     return response.json()


def fetch_all_properties():
    data = get_fourseasons_properties()
    regions = data.get("regions", [])
    all_properties = []
    for region in regions:
        for property in region.get("properties", []):
            all_properties.append(
                {
                    "name": property["name"],
                    "owsCode": property["owsCode"],
                    "tripteaseAPIKey": property.get("tripteaseAPIKey"),
                    "region": region["title"],
                }
            )
    return all_properties


def run_assistant(user_input: str, thread_id: str = None):
    print("Welcome to the FourSeasons Assistant Booking CLI")
    # try:
    #     global_settings()
    #     bookingflow()
    #     print("✅ Booking metadata loaded.")
    # except Exception as e:
    #     print(f"❌ Failed to load booking metadata: {e}")
    #     return

    try:
        if not thread_id:
            thread = openai.beta.threads.create()
            thread_id = thread.id
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return {
            "thread_id": thread_id,
            "response": f"❌ Error during assistant interaction: {e}",
        }

    today = date.today().isoformat()
    date_message = openai.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=f"Remember current date: {today}"
    )

    try:
        openai.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=user_input
        )

        run = openai.beta.threads.runs.create_and_poll(
            thread_id=thread_id, assistant_id=ASSISTANT_ID
        )

        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )

            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for call in tool_calls:
                    name = call.function.name
                    args = json.loads(call.function.arguments)
                    print(f"Tool Calling: {name} with arguments: {args}")

                    try:
                        if name == "check_availability":
                            result = check_availability(
                                owsCode=args["owsCode"],
                                start_date=args["start_date"],
                                end_date=args["end_date"],
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "get_fourseasons_properties":
                            result = fetch_all_properties()
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "confirm_booking_if_available":
                            result = confirm_booking_if_available(
                                start_date=args["start_date"],
                                end_date=args["end_date"],
                                destination=args["destination"],
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "post_result_set":
                            result = post_result_set(
                                start_date=args["start_date"],
                                end_date=args["end_date"],
                                property_name=args["property_name"]
                                or args.get("destination"),
                                persons=args["persons"],
                                room_type=args["room_type"],
                                price=args["price"],
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "get_property_dining":
                            result = get_property_dining(owsCode=args["owsCode"])
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "get_property_experiences":
                            result = get_property_experiences(owsCode=args["owsCode"])
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "post_addons":
                            result = post_addons(
                                result_set_id=args["result_set_id"],
                                sku_id=args["sku_id"],
                                price=args["price"],
                                details=args["product_details"],
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "checkout_result_set":
                            result = checkout_result_set(
                                result_set_id=args["result_set_id"]
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                    except Exception as e:
                        print(f"❌ Tool {name} failed: {e}")
                        tool_outputs.append(
                            {
                                "tool_call_id": call.id,
                                "output": json.dumps(
                                    {"status": "Unavailable", "error": str(e)}
                                ),
                            }
                        )

                openai.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
            elif run_status.status in [
                "expired",
                "failed",
                "cancelled",
                "incomplete",
            ]:
                print(f"❌ Run failed with status: {run_status.status}")
                break

            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        openai.beta.threads.messages.delete(
            message_id=date_message.id, thread_id=thread_id
        )
        for msg in messages.data:
            if msg.role == "assistant":
                print(f"\nAI: {msg.content[0].text.value}")
                return {
                    "thread_id": thread_id,
                    "response": msg.content[0].text.value,
                }

        return {
            "thread_id": thread_id,
            "response": "⚠️ No assistant response found.",
        }
    except Exception as e:
        print(f"❌ Error during assistant interaction: {e}")
        tool_outputs.append(
            {
                "tool_call_id": "",
                "output": json.dumps({"status": "Unavailable", "error": str(e)}),
            }
        )
        return {
            "thread_id": thread_id,
            "response": f"❌ Error during assistant interaction: {e}",
        }


# if __name__ == "__main__":
#     run_assistant()
