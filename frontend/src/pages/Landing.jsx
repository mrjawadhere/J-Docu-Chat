/**
 * Landing page with typewriter animation
 */
import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Upload, MessageCircle, Zap } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { useTypewriter } from '../hooks/useTypewriter';

export const Landing = ({ onGetStarted }) => {
  const { displayText, isComplete } = useTypewriter(
    "Chat with your documents.",
    100,
    1000
  );

  const features = [
    {
      icon: Upload,
      title: "Upload Documents",
      description: "Support for PDF, DOCX, TXT, PPTX, and CSV files up to 20MB each"
    },
    {
      icon: MessageCircle,
      title: "Natural Conversations",
      description: "Ask questions in plain English and get accurate answers from your documents"
    },
    {
      icon: Zap,
      title: "Instant Results",
      description: "Powered by advanced AI with real-time streaming responses"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4">
      <div className="max-w-4xl mx-auto text-center space-y-12">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="space-y-6"
        >
          {/* Logo/Brand */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
            className="text-6xl mb-8"
          >
            📚
          </motion.div>

          {/* Main Heading with Typewriter */}
          <div className="space-y-4">
            <h1 className="text-5xl md:text-6xl font-bold">
              <span className="gradient-text">DocuChat</span>
            </h1>
            
            <div className="h-16 flex items-center justify-center">
              <motion.h2
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-2xl md:text-3xl text-muted-foreground font-light"
              >
                {displayText}
                {!isComplete && (
                  <motion.span
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 1, repeat: Infinity }}
                    className="inline-block w-0.5 h-8 bg-primary ml-1"
                  />
                )}
              </motion.h2>
            </div>
          </div>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.5, duration: 0.6 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
          >
            Transform your documents into an intelligent knowledge base. 
            Upload files, ask questions, and get instant answers powered by advanced AI.
          </motion.p>

          {/* CTA Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 2, duration: 0.6 }}
          >
            <Button
              onClick={onGetStarted}
              size="lg"
              className="text-lg px-8 py-6 ripple group"
            >
              Get Started
              <motion.div
                className="ml-2"
                whileHover={{ x: 5 }}
                transition={{ type: 'spring', stiffness: 400 }}
              >
                <ArrowRight className="w-5 h-5" />
              </motion.div>
            </Button>
          </motion.div>
        </motion.div>

        {/* Features Section */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 2.5, duration: 0.8 }}
          className="grid md:grid-cols-3 gap-6 mt-16"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 2.7 + index * 0.2, duration: 0.6 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className="group"
            >
              <Card className="p-6 h-full glass-effect hover:bg-card/80 transition-all duration-300">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                  className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 mx-auto group-hover:bg-primary/20 transition-colors"
                >
                  <feature.icon className="w-6 h-6 text-primary" />
                </motion.div>
                
                <h3 className="text-lg font-semibold mb-3">{feature.title}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  {feature.description}
                </p>
              </Card>
            </motion.div>
          ))}
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 3.5, duration: 0.6 }}
          className="text-sm text-muted-foreground pt-8"
        >
          <p>
            Powered by OpenAI • Built with React & FastAPI
          </p>
        </motion.div>
      </div>
    </div>
  );
};

