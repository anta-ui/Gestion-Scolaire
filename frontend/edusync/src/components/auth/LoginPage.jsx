import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, User, Lock, GraduationCap, ArrowLeft, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import {
  Container,
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Link,
  Divider
} from '@mui/material';
import Navbar from '../layout/Navbar';
import Footer from '../layout/Footer';
export default function LoginPage() {
  const navigate = useNavigate();
  const { login, loading, error, isAuthenticated } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const darkBlue = '#00008B';
  const elegantRed = '#B22222';
  useEffect(() => {
    // Si l'utilisateur est déjà connecté, rediriger vers le tableau de bord
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (name === 'username') {
      setUsername(value);
    } else if (name === 'password') {
      setPassword(value);
    }
    if (formError) setFormError('');  // Clear error when user starts typing
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    setIsSubmitting(true);

    try {
      const result = await login(username, password);
      if (!result.success) {
        setFormError(result.error || 'Erreur de connexion');
      }
    } catch (error) {
      setFormError('Erreur de connexion au serveur');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleSignUp = () => {
    navigate('/register');
  };

  const handleForgotPassword = () => {
    navigate('/forgot-password');
  };

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box>
      <Navbar />
      <Box
        sx={{
        minHeight: '100vh',
        background: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
        position: 'relative'
      }}
    >
      <Button
        startIcon={<ArrowLeft />}
        onClick={handleBackToHome}
        sx={{
          position: 'absolute',
          top: 24,
          left: 24,
          color: '#6b7280',
          backgroundColor: 'rgba(255, 255, 255, 0.9)',
          backdropFilter: 'blur(10px)',
          '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.95)' }
        }}
      >
        Retour
      </Button>

      <Container maxWidth="sm">
        <Paper
          elevation={1}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(20px)',
            borderRadius: 3,
          }}
        >
          <Box
            sx={{
              width: 60,
              height: 60,
              borderRadius: '50%',
              backgroundColor:  darkBlue,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mb: 2,
              boxShadow: '0 4px 12px rgba(0, 0, 139, 0.3)'
            }}
          >
            <GraduationCap size={30} color="white" />
          </Box>

          <Typography component="h1" variant="h4" sx={{ mb: 1, fontWeight: 700 }}>
            Connexion
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Accédez à votre espace de gestion scolaire
          </Typography>

          {(error || formError) && (
            <Alert 
              severity="error" 
              sx={{ width: '100%', mb: 2 }}
              icon={<AlertCircle size={20} />}
              aria-live="assertive"
            >
              {error || formError}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Nom d'utilisateur"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={handleInputChange}
              disabled={isSubmitting}
              error={!!formError && !username}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <User size={20} color="#9ca3af" />
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />

            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Mot de passe"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={handleInputChange}
              disabled={isSubmitting}
              error={!!formError && username && !password}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Lock size={20} color="#9ca3af" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleTogglePassword}
                      edge="end"
                      size="small"
                    >
                      {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ 
                mt: 3, 
                mb: 2,
                backgroundColor: darkBlue,
                color: 'white',
                borderRadius: 2,
                padding: '12px',
                fontSize: '1rem',
                fontWeight: 500,
                textTransform: 'none',
                '&:hover': {
                  backgroundColor: '#000070',
                },
                '&:disabled': {
                  backgroundColor: '#cccccc',
                }
              }}
              disabled={isSubmitting || loading}
            >
              {loading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
                  Connexion en cours...
                </>
              ) : (
                'Se connecter'
              )}
            </Button>

            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Link
                component="button"
                type="button"
                variant="body2"
                onClick={handleForgotPassword}
                sx={{
                  color: darkBlue,
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  }
                }}
              >
                Mot de passe oublié ?
              </Link>
            </Box>

            <Divider sx={{ my: 3 }}>
              <Typography variant="body2" color="text.secondary">
                OU
              </Typography>
            </Divider>

            <Button
              fullWidth
              variant="outlined"
              onClick={handleSignUp}
              sx={{
                borderRadius: 2,
                padding: '12px',
                fontSize: '1rem',
                fontWeight: 500,
                textTransform: 'none',
                borderColor: '#e5e7eb',
                color: '#374151',
                borderWidth: 2,
                '&:hover': {
                  borderColor: darkBlue,
                  borderWidth: 2,
                  backgroundColor: 'rgba(0, 0, 139, 0.04)',
                }
              }}
            >
              Créer un compte
            </Button>
          </Box>
          
          {/* Footer */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              En vous connectant, vous acceptez nos{' '}
              <Link href="#" sx={{ color: darkBlue }}>
                conditions d'utilisation
              </Link>{' '}
              et notre{' '}
              <Link href="#" sx={{ color: darkBlue }}>
                politique de confidentialité
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Container>
      
    </Box>
    <Footer />
    </Box>
  );
}