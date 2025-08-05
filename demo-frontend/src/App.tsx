import React, { useState } from 'react';
import './App.css';
import ChatBot from './components/ChatBot';
import robotIcon from './assets/images/robotIcon.png'

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 to-black/40 z-0">
        <div className="absolute inset-0 bg-tropical-resort"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 bg-black/80 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-6">
              <div className="flex items-center">
                <div className="w-8 h-8 mr-2">
                  <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <span className="text-lg font-semibold">DOWNLOAD THE APP</span>
              </div>
            </div>
            <nav className="hidden md:flex items-center space-x-8">
              <button className="text-white hover:text-gray-300 transition-colors bg-transparent border-none cursor-pointer">ALL HOTELS AND RESORTS</button>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span>SIGN IN</span>
              </div>
              <div className="flex items-center space-x-2">
                <span>ENGLISH</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </nav>
          </div>
        </div>
      </header>

      {/* Top Banner */}
      <div className="relative z-10 bg-black text-white text-center py-2">
        <span className="text-sm">PLAN YOUR GETAWAY Reopen</span>
      </div>

      {/* Hero Section */}
      <section className="relative z-10 flex items-center justify-center min-h-screen px-4">
        <div className="text-center text-white max-w-4xl">
          <div className="mb-8">
            <div className="w-16 h-16 mx-auto mb-4">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h1 className="text-6xl md:text-8xl font-bold mb-4">
              DISCOVER<br />
              <span className="italic">FOUR SEASONS</span>
            </h1>
          </div>
        </div>
      </section>

      {/* Booking Widget */}
      <section className="relative z-10 -mt-32 mb-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-2xl p-8">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-end">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">DESTINATION</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Find a Hotel or Resort"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <svg className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">CHECK IN — CHECK OUT</label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Check in — Check out"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <svg className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">GUESTS</label>
                <div className="relative">
                  <input
                    type="text"
                    value="1 Room - 2 Adults"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <svg className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <button className="flex-1 bg-gray-600 text-white px-8 py-3 rounded-lg hover:bg-gray-700 transition-colors font-semibold">
                  CHECK RATES
                </button>
                <button className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center hover:bg-white/30 transition-colors">
                  <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom Navigation Icons */}
      <section className="relative z-10 pb-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-wrap justify-center gap-8 md:gap-12">
            {[
              { icon: '🏨', label: 'ALL HOTELS AND RESORTS' },
              { icon: '🏢', label: 'RESIDENCES' },
              { icon: '🏡', label: 'VILLA & RESIDENCE RENTALS' },
              { icon: '🍽️', label: 'DINING' },
              { icon: '✈️', label: 'PRIVATE JET' },
              { icon: '🚢', label: 'YACHTS' },
              { icon: '❄️', label: 'HOLIDAY GETAWAYS' }
            ].map((item, index) => (
              <div key={index} className="text-center text-white hover:text-gray-300 transition-colors cursor-pointer">
                <div className="text-3xl mb-2">{item.icon}</div>
                <div className="text-xs font-medium whitespace-nowrap">{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ChatBot Component */}
      <ChatBot isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
      
      {/* Animated Chat Bubble */}
      <button
        onClick={() => setIsChatOpen(true)}
        className={`fixed bottom-6 right-6 w-16 h-16 bg-white text-black rounded-full shadow-lg hover:bg-gray-100 transition-all duration-300 z-50 flex items-center justify-center ${
          isChatOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'
        }`}
        aria-label="Open chat"
      >
        <img className='h-12' src={robotIcon} alt="" />
      </button>
    </div>
  );
}

export default App;
