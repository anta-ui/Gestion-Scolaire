import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Typography,
  Grid,
  useTheme,
  Fade
} from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

function Hero() {
  const theme = useTheme();
  const navigate = useNavigate();

  // Palette de couleurs
  const darkBlue = '#00008B';
  const elegantRed = '#B22222';

  // Image d'école en arrière-plan
  const backgroundImageUrl = "/images/back4.png";

  return (
    <Box
      sx={{
        position: 'relative',
        overflow: 'hidden',
        pt: { xs: 0, md: 0 },
        pb: { xs: 10, md: 12 },
        backgroundImage: `url(${backgroundImageUrl})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        '&:before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          zIndex: 1
        },
        '&:after': {
          content: '""',
          position: 'absolute',
          bottom: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '80px',
          height: '4px',
          background: `linear-gradient(90deg, ${elegantRed} 0%, white 50%, ${darkBlue} 100%)`,
          borderRadius: '2px',
          zIndex: 2
        }
      }}
    >
      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 2 }}>
        <Grid container justifyContent="center">
          <Grid item xs={12} md={10} lg={8} sx={{ textAlign: 'center' }}>
            <Fade in={true} timeout={800}>
              <Box>
                <Typography
                  component="h1"
                  variant="h2"
                  gutterBottom
                  fontWeight="bold"
                  sx={{
                    fontSize: { xs: '1.5rem', md: '3.5rem' },
                    lineHeight: 1.2,
                    mb: 3,
                    color: 'white'
                  }}
                >
                  Gestion scolaire intelligente et intuitive
                </Typography>
                <Typography 
                  variant="h5" 
                  paragraph
                  sx={{ 
                    fontSize: { xs: '1.1rem', md: '1.25rem' },
                    lineHeight: 1.6,
                    mb: 5,
                    color: 'rgba(255, 255, 255, 0.9)',
                    maxWidth: '800px',
                    mx: 'auto'
                  }}
                >
                  Une plateforme complète pour gérer tous les aspects de votre établissement scolaire : 
                  élèves, enseignants, classes, notes, présences et bien plus encore.
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 3, mb: 6 }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => navigate('/login')}
                    sx={{ 
                      py: 1.5,
                      px: 4,
                      fontSize: '1rem',
                      fontWeight: 600,
                      borderRadius: 0,
                      backgroundColor: 'white',
                      color: darkBlue,
                      border: `2px solid transparent`,
                      borderImage: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%) 1`,
                      position: 'relative',
                      overflow: 'hidden',
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: '-100%',
                        width: '100%',
                        height: '100%',
                        background: `linear-gradient(90deg, transparent, ${elegantRed}20, transparent)`,
                        transition: 'left 0.5s ease'
                      },
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        boxShadow: `0 5px 15px rgba(0, 0, 0, 0.2), 0 0 0 2px ${elegantRed}40`,
                        transform: 'translateY(-2px)',
                        '&:before': {
                          left: '100%'
                        }
                      },
                      transition: 'all 0.3s ease'
                    }}
                    endIcon={<ArrowForwardIcon />}
                  >
                    Commencer maintenant
                  </Button>
                  <Button
                    variant="outlined"
                    size="large"
                    onClick={() => navigate('/demo')}
                    sx={{ 
                      py: 1.5,
                      px: 4,
                      fontSize: '1rem',
                      fontWeight: 600,
                      borderRadius: 0,
                      backgroundColor: 'white',
                      color: darkBlue,
                      border: `2px solid transparent`,
                      borderImage: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%) 1`,
                      position: 'relative',
                      overflow: 'hidden',
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: '-100%',
                        width: '100%',
                        height: '100%',
                        background: `linear-gradient(90deg, transparent, ${elegantRed}20, transparent)`,
                        transition: 'left 0.5s ease'
                      },
                      '&:hover': {
                        backgroundColor: 'rgba(255, 255, 255, 0.95)',
                        boxShadow: `0 5px 15px rgba(0, 0, 0, 0.2), 0 0 0 2px ${elegantRed}40`,
                        transform: 'translateY(-2px)',
                        '&:before': {
                          left: '100%'
                        }
                      },
                      transition: 'all 0.3s ease'
                    }}
                    startIcon={<PlayArrowIcon />}
                  >
                    Voir la démo
                  </Button>
                </Box>
              </Box>
            </Fade>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default Hero;