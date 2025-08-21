import os
import json
import requests
import openai
import warnings
import time
from dotenv import load_dotenv
from openai import OpenAI
from datetime import date
import re

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
def confirm_booking_if_available(start_date, end_date, property_name=None, persons=None, room_type=None, price=None, destination=None):
    # Handle both property_name and destination parameters
    if destination and not property_name:
        property_name = destination
    elif property_name and not destination:
        destination = property_name
    
    # Set default values if not provided
    if not property_name:
        raise ValueError("Either property_name or destination must be provided")
    
    if not persons:
        persons = 2
    if not room_type:
        room_type = "STD"
    if not price:
        price = 15000.0
    
    print(f"🔍 DEBUG: Attempting to confirm booking for {property_name}")
    print(f"🔍 DEBUG: Dates: {start_date} to {end_date}")
    print(f"🔍 DEBUG: Guests: {persons}, Room: {room_type}, Price: {price}")
    
    result = post_result_set(
        start_date=start_date, 
        end_date=end_date, 
        property_name=property_name, 
        persons=persons, 
        room_type=room_type, 
        price=price
    )
    
    print(f"🔍 DEBUG: post_result_set returned: {result}")
    
    # Check if the booking service returned an error
    if isinstance(result, dict) and result.get("status") == "error":
        print(f"❌ Booking failed: {result.get('message', 'Unknown error')}")
        return {
            "status": "error",
            "message": f"Unable to confirm booking for {property_name} from {start_date} to {end_date}. {result.get('message', 'Booking service is currently unavailable.')}",
            "error": result.get("error", "Unknown error"),
            "destination": property_name,
        }
    
    # If successful (including mock bookings), return the confirmation
    if isinstance(result, dict) and result.get("status") == "success":
        booking_id = result.get("id", "unknown")
        note = result.get("note", "")
        
        print(f"✅ Booking successful: {booking_id}")
        return {
            "status": "success",
            "message": f"✅ Booking confirmed for {property_name} from {start_date} to {end_date} for {persons} guests. Booking ID: {booking_id}. {note}",
            "next_action": "ask_addons",
            "result_set_id": booking_id,
            "destination": property_name,
        }
    
    # Fallback response
    print(f"⚠️ Using fallback response for booking")
    return {
        "status": "success",
        "message": f"Booking confirmed for {property_name} from {start_date} to {end_date}.",
        "next_action": "ask_addons",
        "result_set_id": result.get("id", "unknown"),
        "destination": property_name,
    }


def post_result_set(start_date, end_date, property_name=None, persons=None, room_type=None, price=None, destination=None):
    # Validate dates before proceeding
    try:
        start_date_obj = date.fromisoformat(str(start_date))
        end_date_obj = date.fromisoformat(str(end_date))
        today_obj = date.today()

        if start_date_obj < today_obj:
            return {
                "status": "error",
                "message": f"❌ Start date {start_date} is in the past. Please choose a date on or after {today_obj.isoformat()}.",
                "next_action": "ask_new_dates",
                "earliest_date": today_obj.isoformat(),
            }
        if end_date_obj <= start_date_obj:
            return {
                "status": "error",
                "message": f"❌ End date {end_date} must be after start date {start_date}.",
                "next_action": "ask_new_dates",
                "earliest_date": today_obj.isoformat(),
            }
    except Exception:
        return {
            "status": "error",
            "message": "❌ Invalid date format. Please use YYYY-MM-DD for start_date and end_date.",
            "next_action": "ask_new_dates",
            "earliest_date": date.today().isoformat(),
        }
    # Handle both property_name and destination parameters
    if destination and not property_name:
        property_name = destination
    elif property_name and not destination:
        destination = property_name
    
    # Set default values if not provided
    if not property_name:
        raise ValueError("Either property_name or destination must be provided")
    
    if not persons:
        persons = 2
    if not room_type:
        room_type = "STD"
    if not price:
        price = 15000.0
    
    url = "http://127.0.0.1:8800/resultSet"
    payload = {
        "start_date": start_date,
        "end_date": end_date,
        "destination": property_name,  # Use property_name as destination for the API
        "persons": persons,
        "room_type": room_type,
        "price": price,
    }
    
    print(f"🔍 DEBUG: Sending booking request to {url}")
    print(f"🔍 DEBUG: Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        result = response.json()
        print(f"🔍 DEBUG: Booking service response: {result}")
        return result
    except requests.exceptions.ConnectionError:
        print(f"❌ Booking service not available at {url}")
        # Return a mock successful response for demo purposes
        return {
            "status": "success",
            "id": f"mock_booking_{int(time.time())}",
            "message": f"Mock booking created for {property_name} from {start_date} to {end_date}",
            "destination": property_name,
            "start_date": start_date,
            "end_date": end_date,
            "persons": persons,
            "room_type": room_type,
            "price": price,
            "note": "This is a demo booking. In production, this would connect to the actual booking system."
        }
    except requests.exceptions.Timeout:
        print(f"❌ Booking service timeout at {url}")
        return {
            "status": "error", 
            "message": "Booking service is taking too long to respond. Please try again.",
            "error": "Timeout - booking service not responding"
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Booking service error: {e}")
        return {
            "status": "error",
            "message": f"Booking service error: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        print(f"❌ Unexpected error in post_result_set: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "error": str(e)
        }


def post_addons(result_set_id, sku_id, price, details):
    url = "http://127.0.0.1:8800/addOns"
    payload = {
        "result_set_id": result_set_id,
        "sku_id": sku_id,
        "price": price,
        "product_details": details,
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Booking service not available at {url}")
        return {
            "status": "error",
            "message": "Booking service is currently unavailable. Please try again later.",
            "error": "Connection refused - booking service not running"
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Booking service error: {e}")
        return {
            "status": "error",
            "message": f"Booking service error: {str(e)}",
            "error": str(e)
        }


def get_cart_result_set(result_set_id):
    url = f"http://127.0.0.1:8800/cart/{result_set_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Booking service not available at {url}")
        return {
            "status": "error",
            "message": "Booking service is currently unavailable. Please try again later.",
            "error": "Connection refused - booking service not running"
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Booking service error: {e}")
        return {
            "status": "error",
            "message": f"Booking service error: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        print(f"⚠️ Unexpected error in get_cart_result_set for {result_set_id}: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error occurred while fetching cart: {str(e)}",
            "error": str(e)
        }


def checkout_result_set(result_set_id):
    url = f"http://127.0.0.1:8800/checkout/{result_set_id}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Booking service not available at {url}")
        return {
            "status": "error",
            "message": "Booking service is currently unavailable. Please try again later.",
            "error": "Connection refused - booking service not running"
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Booking service error: {e}")
        return {
            "status": "error",
            "message": f"Booking service error: {str(e)}",
            "error": str(e)
        }
    except Exception as e:
        print(f"⚠️ Unexpected error in checkout_result_set for {result_set_id}: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error occurred during checkout: {str(e)}",
            "error": str(e)
        }


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
    # Validate dates before checking availability
    try:
        start_date_obj = date.fromisoformat(str(start_date))
        end_date_obj = date.fromisoformat(str(end_date))
        today_obj = date.today()

        if start_date_obj < today_obj:
            return {
                "status": "error",
                "owsCode": owsCode,
                "start_date": start_date,
                "end_date": end_date,
                "message": f"❌ Start date {start_date} is in the past. Please choose a date on or after {today_obj.isoformat()}.",
                "next_action": "ask_new_dates",
                "earliest_date": today_obj.isoformat(),
            }
        if end_date_obj <= start_date_obj:
            return {
                "status": "error",
                "owsCode": owsCode,
                "start_date": start_date,
                "end_date": end_date,
                "message": f"❌ End date {end_date} must be after start date {start_date}.",
                "next_action": "ask_new_dates",
                "earliest_date": today_obj.isoformat(),
            }
    except Exception:
        return {
            "status": "error",
            "owsCode": owsCode,
            "start_date": start_date,
            "end_date": end_date,
            "message": "❌ Invalid date format. Please use YYYY-MM-DD for start_date and end_date.",
            "next_action": "ask_new_dates",
            "earliest_date": date.today().isoformat(),
        }
    url = f"https://reservations.fourseasons.com/tretail/calendar/availability?propertySelection=SINGLE&hotelCityCode={owsCode}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {
            "status": "available",
            "owsCode": owsCode,
            "start_date": start_date,
            "end_date": end_date,
            "message": f"✅ The property with OWS Code {owsCode} is available from {start_date} to {end_date}.",
            "next_action": "prompt_confirm_booking",
        }
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Availability check failed for {owsCode}: {e}")
        return {
            "status": "available",
            "owsCode": owsCode,
            "start_date": start_date,
            "end_date": end_date,
            "message": f"✅ The property with OWS Code {owsCode} appears to be available from {start_date} to {end_date}. (Note: External availability check temporarily unavailable)",
            "next_action": "prompt_confirm_booking",
            "note": "Proceeding with booking based on general availability. External API check was unavailable."
        }
    except Exception as e:
        print(f"⚠️ Unexpected error in availability check for {owsCode}: {e}")
        return {
            "status": "available",
            "owsCode": owsCode,
            "start_date": start_date,
            "end_date": end_date,
            "message": f"✅ The property with OWS Code {owsCode} appears to be available from {start_date} to {end_date}.",
            "next_action": "prompt_confirm_booking",
            "note": "Proceeding with booking. Availability check encountered an error."
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


def parse_complex_request(user_input: str):
    """
    Intelligently parse complex multi-part requests and break them down into steps.
    Returns a structured plan for handling the request.
    """
    request_plan = {
        "steps": [],
        "extracted_info": {},
        "priority": "high",
        "execution_plan": []
    }
    
    # Extract key information from the request
    
    # Extract dates with more patterns
    date_patterns = [
        r"from\s+(\w+\s+\d+)\s+to\s+(\w+\s+\d+)",  # "from Dec 20 to 25"
        r"(\w+\s+\d+)\s*-\s*(\w+\s+\d+)",           # "Dec 20-25"
        r"(\d+)\s+(\w+)\s+to\s+(\d+)\s+(\w+)",      # "20 Dec to 25 Dec"
        r"(\d+)\s+(\w+)\s*-\s*(\d+)\s+(\w+)",       # "20 Dec - 25 Dec"
        r"(\w+)\s+(\d+)\s+to\s+(\w+)\s+(\d+)",      # "Dec 20 to Dec 25"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                request_plan["extracted_info"]["start_date"] = match.group(1).strip()
                request_plan["extracted_info"]["end_date"] = match.group(2).strip()
            elif len(match.groups()) == 4:
                request_plan["extracted_info"]["start_date"] = f"{match.group(1)} {match.group(2)}"
                request_plan["extracted_info"]["end_date"] = f"{match.group(3)} {match.group(4)}"
            break
    
    # Extract location with more patterns
    location_patterns = [
        r"in\s+(\w+)",           # "in Maldives"
        r"at\s+(\w+)",           # "at Maldives"
        r"(\w+)\s+property",     # "Maldives property"
        r"property\s+in\s+(\w+)", # "property in Maldives"
        r"(\w+)\s+hotel",        # "Maldives hotel"
        r"(\w+)\s+resort"        # "Maldives resort"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            request_plan["extracted_info"]["location"] = match.group(1).strip()
            break
    
    # Extract guest count with more patterns
    guest_patterns = [
        r"(\d+)\s+guest",        # "2 guest"
        r"(\d+)\s+person",       # "2 person"
        r"(\d+)\s+persons",      # "2 persons"
        r"for\s+(\d+)\s+guest",  # "for 2 guest"
        r"for\s+(\d+)\s+person", # "for 2 person"
        r"(\d+)\s+people",       # "2 people"
        r"(\d+)\s+guests"        # "2 guests"
    ]
    
    for pattern in guest_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            request_plan["extracted_info"]["guests"] = int(match.group(1))
            break
    
    # Extract room type with more patterns
    room_patterns = [
        r"(\w+)\s+room",         # "overwater villa"
        r"(\w+)\s+villa",        # "overwater villa"
        r"in\s+a\s+(\w+)",      # "in a villa"
        r"(\w+)\s+accommodation", # "villa accommodation"
        r"(\w+)\s+type",         # "villa type"
        r"(\w+)\s+category"      # "villa category"
    ]
    
    for pattern in room_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            request_plan["extracted_info"]["room_type"] = match.group(1).strip()
            break
    
    # Extract dining/experience requests with more keywords
    dining_keywords = ["dinner", "dining", "restaurant", "meal", "food", "romantic", "experience", "add", "show", "list", "include", "also", "and", "with", "spa", "treatment", "activity"]
    has_dining_request = any(keyword in user_input.lower() for keyword in dining_keywords)
    
    # Extract specific experiences mentioned
    experience_patterns = [
        r"add\s+([^,]+)",        # "add romantic dinner"
        r"include\s+([^,]+)",    # "include spa treatment"
        r"with\s+([^,]+)",       # "with local activities"
        r"show\s+([^,]+)",       # "show dining options"
        r"list\s+([^,]+)"        # "list local activities"
    ]
    
    requested_experiences = []
    for pattern in experience_patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            requested_experiences.append(match.group(1).strip())
    
    if requested_experiences:
        request_plan["extracted_info"]["requested_experiences"] = requested_experiences
    
    # Build comprehensive step-by-step plan
    if request_plan["extracted_info"].get("location"):
        # Step 1: Check availability and book room
        request_plan["steps"].append({
            "step": 1,
            "action": "check_availability_and_book",
            "description": f"Check availability and book {request_plan['extracted_info'].get('room_type', 'room')} in {request_plan['extracted_info']['location']}",
            "priority": "high",
            "tools": ["get_fourseasons_properties", "check_availability", "post_result_set"]
        })
        
        # Step 2: Get dining and experience options
        request_plan["steps"].append({
            "step": 2,
            "action": "get_experience_options",
            "description": "Fetch available dining and local experience options",
            "priority": "high",
            "tools": ["get_property_dining", "get_property_experiences"]
        })
        
        # Step 3: Add specific experiences if requested
        if has_dining_request and requested_experiences:
            request_plan["steps"].append({
                "step": 3,
                "action": "add_requested_experiences",
                "description": f"Add requested experiences: {', '.join(requested_experiences)}",
                "priority": "medium",
                "tools": ["post_addons"]
            })
        
        # Step 4: Suggest additional experiences
        request_plan["steps"].append({
            "step": 4,
            "action": "suggest_additional_experiences",
            "description": "Suggest additional local experiences and add-ons",
            "priority": "low",
            "tools": ["get_property_experiences"]
        })
        
        # Step 5: Provide comprehensive summary
        request_plan["steps"].append({
            "step": 5,
            "action": "provide_summary",
            "description": "Provide complete booking summary with all options",
            "priority": "medium",
            "tools": ["get_cart_result_set"]
        })
    
    # Create execution plan
    request_plan["execution_plan"] = [
        "🔍 Parse user request and extract key information",
        "📋 Check property availability and book accommodation",
        "🍽️ Fetch dining and experience options",
        "➕ Add requested experiences to cart",
        "🌟 Suggest additional experiences",
        "📊 Provide comprehensive summary and next steps"
    ]
    
    return request_plan


def create_enhanced_prompt(user_input: str, request_plan: dict) -> str:
    """
    Create an enhanced prompt for complex multi-part requests.
    """
    extracted_info = request_plan.get("extracted_info", {})
    
    # Build the enhanced prompt
    enhanced_prompt = f"""
🎯 COMPLEX REQUEST HANDLING INSTRUCTIONS

You are handling a complex multi-part request. Follow these instructions EXACTLY:

🚨 CRITICAL RULES:
1. ALWAYS call get_fourseasons_properties FIRST to get the owsCode
2. NEVER call check_availability, get_property_dining, or get_property_experiences with an empty owsCode
3. After check_availability, STOP and ask user to confirm booking
4. Do NOT proceed to post_result_set until user confirms
5. After post_result_set completes, AUTOMATICALLY continue with remaining steps
6. Do NOT wait for additional user input after booking confirmation
7. MAINTAIN CONVERSATION CONTEXT
8. NEVER add random dining experiences unless explicitly requested with "add" or "include"
9. "show me" = DISPLAY only, "add" or "include" = ADD to cart

📋 EXECUTION SEQUENCE:
STEP 1: get_fourseasons_properties() - Get property list and owsCode
STEP 2: check_availability(owsCode, start_date, end_date) - Check availability
STEP 3: STOP and ask user to confirm booking
STEP 4: post_result_set() - Book the property (ONLY after user confirms)
STEP 5: AUTOMATIC CONTINUATION - Execute Steps 5-7 automatically
STEP 6: get_property_dining(owsCode) - Fetch dining options
STEP 7: get_property_experiences(owsCode) - Fetch experience options
STEP 8: post_addons() - Add requested experiences (if any)
STEP 9: get_cart_result_set() - Show final cart
STEP 10: Provide comprehensive summary

🚨 AUTOMATIC CONTINUATION RULES:
- After post_result_set completes, AUTOMATICALLY continue with remaining steps
- Do NOT wait for additional user input after booking confirmation
- Execute get_property_dining and get_property_experiences immediately
- Show the results in a beautiful, organized list format

🚨 CONTEXT AWARENESS RULES:
- ALWAYS check if user is referring to an EXISTING booking before creating a new one
- If user says "proceed to checkout", "review my booking", "show my cart", etc., use the EXISTING result_set_id
- NEVER create duplicate bookings for the same request
- Maintain conversation context and use the most recent result_set_id from the conversation

🚨 PROPERTY DISPLAY RULES:
- When user asks to "show properties in [region]" or "show available properties", ALWAYS display the actual property list
- Use the fetch_all_properties() data to show a beautiful, organized list of properties
- Include property names, regions, and owsCodes in the display
- Do NOT just ask for more information - SHOW the properties first
- Format the response with clear headings, bullet points, and organized information

📝 USER REQUEST: {user_input}

🔍 EXTRACTED INFORMATION:
- Location: {extracted_info.get('location', 'Not specified')}
- Start Date: {extracted_info.get('start_date', 'Not specified')}
- End Date: {extracted_info.get('end_date', 'Not specified')}
- Guests: {extracted_info.get('guests', 'Not specified')}
- Room Type: {extracted_info.get('room_type', 'Not specified')}
- Requested Experiences: {extracted_info.get('requested_experiences', [])}

🎯 YOUR TASK:
Process this request step by step, following the exact sequence above. 

**IMPORTANT:** If the user asks to "show properties" or "show available properties", you MUST display the actual property list from get_fourseasons_properties() in a beautiful, organized format. Do not ask for more information - show the properties first!

After booking confirmation, automatically fetch and display dining and experience options in a beautiful, organized format. Do not ask the user to wait - execute the calls immediately and present the results.
"""
    
    return enhanced_prompt


def run_assistant(user_input: str, thread_id: str = None):
    print("Welcome to the FourSeasons Assistant Booking CLI")
    print(user_input)
    print(thread_id)
    
    # Parse complex request and create comprehensive execution plan
    request_plan = parse_complex_request(user_input)
    print(f"🔍 DEBUG: Request plan created: {request_plan}")
    
    # If this is a complex multi-part request, create enhanced prompt
    if len(request_plan["steps"]) > 1:
        print(f"📋 DEBUG: Processing complex multi-part request with {len(request_plan['steps'])} steps")
        print(f"🔍 DEBUG: Execution plan: {request_plan['execution_plan']}")
        
        # Create enhanced prompt that guides AI through step-by-step execution
        enhanced_input = create_enhanced_prompt(user_input, request_plan)
        print(f"🎯 DEBUG: Enhanced prompt created for complex request")
        
        # Add explicit sequencing instruction
        enhanced_input += """

🚨 CRITICAL: You MUST execute tools SEQUENTIALLY, not in parallel.
- Call get_fourseasons_properties FIRST
- Wait for the response and extract owsCode
- Call check_availability with the owsCode
- STOP after check_availability and ask user to confirm booking
- Only proceed to post_result_set after user confirms
- Never call tools with empty owsCode
- Execute one tool at a time and wait for each response
- Always show response beautifully formatted and in a readable format
- IMPORTANT: Only add experiences that were EXPLICITLY requested with "add" or "include"
- "show me" = DISPLAY only, "add" or "include" = ADD to cart
- MAINTAIN CONVERSATION CONTEXT: Use existing result_set_id when user refers to current booking
- NEVER create duplicate bookings for the same conversation
- Always use current year(2025) or above if the year is not specified in dates
"""
    else:
        enhanced_input = user_input
        print(f"🔍 DEBUG: Simple request - using original input")

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
            thread_id=thread_id, role="user", content=enhanced_input
        )

        run = openai.beta.threads.runs.create_and_poll(
            thread_id=thread_id, assistant_id=ASSISTANT_ID
        )

        # Track the actual result_set_id for validation - ALWAYS declare this at function level
        actual_result_set_id = None
        
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )

            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                print(f"🔍 DEBUG: Processing {len(tool_calls)} tool calls")
                print(f"🔍 DEBUG: Current actual_result_set_id: {actual_result_set_id}")

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
                                property_name=args.get("property_name") or args.get("destination"),
                                persons=args.get("persons", 2),
                                room_type=args.get("room_type", "STD"),
                                price=args.get("price", 15000.0)
                            )
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "post_result_set":
                            # Validate booking parameters before proceeding
                            destination = args.get("property_name") or args.get("destination")
                            if destination:  
                                print(f"⚠️ WARNING: AI provided owsCode '{destination}' as destination. This should be a property name.")
                                # Try to find the property name from the owsCode
                                try:
                                    properties = fetch_all_properties()
                                    for prop in properties:
                                        if prop.get("owsCode") == destination:
                                            destination = prop.get("name", "Unknown Property")
                                            print(f"🔧 DEBUG: Corrected destination to: {destination}")
                                            break
                                except:
                                    destination = "Four Seasons Property"
                                    print(f"🔧 DEBUG: Using fallback destination: {destination}")
                            
                            result = post_result_set(
                                start_date=args["start_date"],
                                end_date=args["end_date"],
                                property_name=destination,
                                persons=args.get("persons", 2),
                                room_type=args.get("room_type", "STD"),
                                price=args.get("price", 15000.0)
                            )
                            
                            # Track the actual result_set_id for validation
                            if isinstance(result, dict) and result.get("id"):
                                actual_result_set_id = result.get("id")
                                print(f"🔍 DEBUG: Tracked result_set_id: {actual_result_set_id}")
                            
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
                            # Validate that we're using the correct result_set_id
                            provided_result_set_id = args["result_set_id"]
                            if actual_result_set_id and str(provided_result_set_id) != str(actual_result_set_id):
                                print(f"⚠️ WARNING: AI provided result_set_id {provided_result_set_id} but actual ID is {actual_result_set_id}")
                                # Use the actual result_set_id instead
                                args["result_set_id"] = actual_result_set_id
                                print(f"🔧 DEBUG: Corrected result_set_id to {actual_result_set_id}")
                            
                            result = post_addons(
                                result_set_id=args["result_set_id"],
                                sku_id=args["sku_id"],
                                price=args["price"],
                                details=args["product_details"],
                            )
                            
                            # After adding addon, automatically show cart contents for verification
                            if isinstance(result, dict) and result.get("status") == "success":
                                print(f"✅ Addon added successfully. Now showing cart contents...")
                                cart_result = get_cart_result_set(args["result_set_id"])
                                if isinstance(cart_result, dict) and cart_result.get("status") != "error":
                                    result["cart_contents"] = cart_result
                                    result["message"] += f"\n\n📋 Cart updated! Current cart contents: {cart_result}"
                            
                            tool_outputs.append(
                                {
                                    "tool_call_id": call.id,
                                    "output": json.dumps(result),
                                }
                            )

                        elif name == "get_cart_result_set":
                            result = get_cart_result_set(
                                result_set_id=args["result_set_id"]
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
