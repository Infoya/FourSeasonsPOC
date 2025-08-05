# Four Seasons Assistant Demo Frontend

A modern React + TypeScript + Tailwind CSS demo homepage featuring a Four Seasons AI chatbot interface.

## Features

- 🏨 **Four Seasons Branded Design** - Luxury hotel aesthetic with modern UI
- 🤖 **AI Chatbot Interface** - Interactive chat modal with realistic responses
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- ⚡ **Real-time Chat** - Smooth messaging experience with loading states
- 🎨 **Tailwind CSS** - Modern styling with utility-first approach

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Fast build tool (via Create React App)

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   └── ChatBot.tsx          # Main chatbot component
├── services/
│   └── api.ts              # API service for backend integration
├── App.tsx                 # Main application component
├── App.css                 # Global styles
└── index.css              # Tailwind CSS imports
```

## Chatbot Integration

The chatbot is designed to integrate with your Python backend:

1. **API Endpoint**: Configured to connect to `http://localhost:5000/chat`
2. **Fallback Responses**: Local responses for demo purposes
3. **Error Handling**: Graceful fallback when backend is unavailable

### Backend Integration

To connect with your Python backend:

1. Update the `API_BASE_URL` in `src/services/api.ts`
2. Ensure your backend exposes a `/chat` endpoint
3. The endpoint should accept POST requests with JSON body: `{ "message": "user input" }`
4. Return JSON response: `{ "response": "bot response" }`

## Customization

### Styling
- Modify Tailwind classes in components
- Update color scheme in `tailwind.config.js`
- Add custom CSS in `App.css`

### Chatbot Responses
- Edit response logic in `src/services/api.ts`
- Add new conversation flows
- Customize the welcome message

### Branding
- Update Four Seasons branding in `App.tsx`
- Modify header content and navigation
- Change hero section messaging

## Demo Features

The demo includes:
- **Welcome Message**: Greets users with Four Seasons branding
- **Booking Assistance**: Helps with hotel reservations
- **Destination Info**: Provides information about properties
- **Dining & Experiences**: Information about hotel services
- **Responsive Design**: Works across all device sizes

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Code Style

- TypeScript for type safety
- Functional components with hooks
- Tailwind CSS for styling
- ESLint for code quality

## License

This project is for demonstration purposes.
