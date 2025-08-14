import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Card,
  CardContent,
  Fade,
  useTheme,
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import { useAuth } from '../hooks/useAuth';

const LoginPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  // Get the redirect path from location state (for protected route redirects)
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleLoginSuccess = () => {
    navigate(from, { replace: true });
  };

  const handleRegisterSuccess = () => {
    navigate(from, { replace: true });
  };

  const handleToggleForm = () => {
    setShowRegister(!showRegister);
  };

  if (isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: theme.palette.mode === 'dark' 
          ? 'linear-gradient(135deg, #0d1421 0%, #1e293b 50%, #334155 100%)'
          : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%)',
        display: 'flex',
        alignItems: 'center',
        py: 4,
      }}
    >
      <Container maxWidth="sm">
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{
              fontWeight: 'bold',
              background: theme.palette.mode === 'dark'
                ? 'linear-gradient(45deg, #3b82f6 30%, #1e40af 90%)'
                : 'linear-gradient(45deg, #1e40af 30%, #3b82f6 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1,
            }}
          >
            CLO Management System
          </Typography>
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ mb: 4 }}
          >
            Professional Portfolio Management Platform
          </Typography>
        </Box>

        <Card
          elevation={8}
          sx={{
            backdropFilter: 'blur(20px)',
            backgroundColor: theme.palette.mode === 'dark'
              ? 'rgba(15, 23, 42, 0.8)'
              : 'rgba(255, 255, 255, 0.9)',
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 3,
          }}
        >
          <CardContent sx={{ p: 0 }}>
            <Fade in={!showRegister} timeout={300}>
              <Box sx={{ display: showRegister ? 'none' : 'block' }}>
                <LoginForm
                  onSuccess={handleLoginSuccess}
                  onRegisterClick={handleToggleForm}
                />
              </Box>
            </Fade>

            <Fade in={showRegister} timeout={300}>
              <Box sx={{ display: showRegister ? 'block' : 'none' }}>
                <RegisterForm
                  onSuccess={handleRegisterSuccess}
                  onLoginClick={handleToggleForm}
                />
              </Box>
            </Fade>
          </CardContent>
        </Card>

        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            © 2024 CLO Management System. All rights reserved.
          </Typography>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Secure • Compliant • Professional
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default LoginPage;