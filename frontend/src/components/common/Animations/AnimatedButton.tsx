/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * AnimatedButton - Enhanced button component with advanced interactions
 * 
 * Features:
 * - Smooth hover and tap animations
 * - Loading state with pulsing animation
 * - Configurable pulse effect on hover
 * - Spring-based interactions for organic feel
 * - Support for all Material-UI button variants
 * - Reduced motion support
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Button, ButtonProps, CircularProgress } from '@mui/material';
import { AnimatedButtonProps } from './types';
import { useEnhancedAnimation, useLoadingAnimation, useGestureAnimation } from './hooks';
import { buttonVariants } from './variants';

const AnimatedButton: React.FC<AnimatedButtonProps & ButtonProps> = ({
  children,
  loading = false,
  variant = 'contained',
  size = 'medium',
  pulseOnHover = false,
  delay = 0,
  className,
  disabled,
  onClick,
  ...buttonProps
}) => {
  const { shouldAnimate } = useEnhancedAnimation();
  const { variants: loadingVariants, controls } = useLoadingAnimation(loading);
  const gestureProps = useGestureAnimation();

  // Custom button variants with pulse effect
  const customButtonVariants = {
    ...buttonVariants,
    hover: {
      ...buttonVariants.hover,
      ...(pulseOnHover && {
        scale: [1.05, 1.08, 1.05],
        transition: {
          scale: {
            repeat: Infinity,
            duration: 1.5,
            ease: 'easeInOut',
          },
          boxShadow: {
            duration: 0.2,
          },
        },
      }),
    },
  };

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (loading || disabled) return;
    onClick?.(event);
  };

  if (!shouldAnimate) {
    return (
      <Button
        {...buttonProps}
        variant={variant}
        size={size}
        disabled={disabled || loading}
        onClick={handleClick}
        className={className}
        startIcon={loading ? <CircularProgress size={16} /> : buttonProps.startIcon}
      >
        {children}
      </Button>
    );
  }

  return (
    <motion.div
      variants={loadingVariants}
      animate={controls}
      initial="idle"
      transition={{
        delay,
      }}
      style={{
        display: 'inline-block',
      }}
    >
      <motion.div
        variants={customButtonVariants}
        initial="idle"
        whileHover={!disabled && !loading ? "hover" : "idle"}
        whileTap={!disabled && !loading ? "tap" : "idle"}
        {...(shouldAnimate && gestureProps)}
      >
        <Button
          {...buttonProps}
          variant={variant}
          size={size}
          disabled={disabled || loading}
          onClick={handleClick}
          className={className}
          startIcon={loading ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: 'linear',
              }}
            >
              <CircularProgress size={16} />
            </motion.div>
          ) : buttonProps.startIcon}
          sx={{
            position: 'relative',
            overflow: 'hidden',
            ...buttonProps.sx,
          }}
        >
          {children}
          
          {/* Ripple effect overlay */}
          {shouldAnimate && !disabled && !loading && (
            <motion.div
              initial={{ scale: 0, opacity: 0.5 }}
              animate={{ scale: 0, opacity: 0.5 }}
              whileTap={{ scale: 1, opacity: 0 }}
              transition={{ duration: 0.4 }}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(255, 255, 255, 0.3)',
                borderRadius: 'inherit',
                pointerEvents: 'none',
              }}
            />
          )}
        </Button>
      </motion.div>
    </motion.div>
  );
};

export default AnimatedButton;