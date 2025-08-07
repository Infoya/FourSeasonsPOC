// API service for communicating with the Python backend
const API_BASE_URL = 'http://127.0.0.1:4000'; // Updated to match your backend port

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface ApiResponse {
  thread_id: string;
  response: string;
}

export const sendMessage = async (message: string, threadId?: string): Promise<ApiResponse> => {
  try {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add thread ID if provided for conversation continuity
    if (threadId) {
      headers['threadid'] = threadId;
    }

    // For initialization, send a welcome message if the message is empty
    const trimmedMessage = message.trim();
    const userInput = trimmedMessage === '' ? 'Hi' : trimmedMessage;

    const response = await fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ user_input: userInput }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      thread_id: data.thread_id || '',
      response: data.response || 'Sorry, I couldn\'t process your request.'
    };
  } catch (error) {
    console.error('API Error:', error);
    // Fallback to local response for demo
    return {
      thread_id: '',
      response: getLocalResponse(message)
    };
  }
};

// Local response function for demo purposes (fallback when backend is unavailable)
const getLocalResponse = (message: string): string => {
  const input = message.toLowerCase();
  
  if (input.includes('book') || input.includes('reservation')) {
    return 'I\'d be delighted to assist you with your Four Seasons reservation. Please share your preferred destination, travel dates, and number of guests, and I\'ll help you find the perfect accommodation.';
  } else if (input.includes('maldives')) {
    return 'The Four Seasons Maldives offers two extraordinary properties: Kuda Huraa and Landaa Giraavaru. Both feature overwater villas, world-class dining, and pristine beaches. When would you like to experience this paradise?';
  } else if (input.includes('price') || input.includes('cost') || input.includes('rate')) {
    return 'Our rates reflect the exceptional luxury and service you\'ll experience. They vary by property, season, and room category. I\'d be happy to provide specific pricing for your preferred destination and dates.';
  } else if (input.includes('dining') || input.includes('restaurant') || input.includes('food')) {
    return 'Four Seasons properties feature award-winning restaurants with world-renowned chefs. From fine dining to casual beachfront experiences, we offer exceptional culinary journeys. Which destination interests you?';
  } else if (input.includes('spa') || input.includes('wellness')) {
    return 'Our spas offer transformative wellness experiences with expert therapists and luxurious treatments. Many properties feature signature spa programs unique to their location.';
  } else if (input.includes('experience') || input.includes('activity') || input.includes('adventure')) {
    return 'We offer curated experiences at every property - from cultural immersion to adventure activities. Whether you seek relaxation or excitement, our concierge team can arrange unforgettable moments.';
  } else if (input.includes('hello') || input.includes('hi') || input.includes('welcome')) {
    return 'Welcome to Four Seasons! I\'m your personal concierge, ready to help you plan the perfect luxury experience. How may I assist you today?';
  } else if (input.includes('bora bora') || input.includes('tahiti')) {
    return 'Four Seasons Bora Bora is a true paradise with overwater bungalows, crystal-clear lagoons, and Mount Otemanu views. It\'s perfect for honeymoons and romantic getaways.';
  } else if (input.includes('hawaii') || input.includes('maui') || input.includes('lanai')) {
    return 'Our Hawaiian properties offer the perfect blend of luxury and authentic Aloha spirit. From Maui\'s pristine beaches to Lanai\'s secluded paradise, each location provides unique experiences.';
  } else {
    return 'Thank you for your inquiry! I\'m here to help you plan your perfect Four Seasons experience. You can ask me about reservations, destinations, dining, spa treatments, activities, or any aspect of your luxury journey.';
  }
}; 