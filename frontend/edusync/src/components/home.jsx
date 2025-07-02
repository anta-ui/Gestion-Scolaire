import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Typography,
  Grid,
  Paper,
  useTheme
} from '@mui/material';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import SchoolIcon from '@mui/icons-material/School';
import PeopleIcon from '@mui/icons-material/People';
import AssessmentIcon from '@mui/icons-material/Assessment';
import EventNoteIcon from '@mui/icons-material/EventNote';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Hero from './layout/Hero';
import Navbar from './layout/Navbar';
import Footer from './layout/Footer';

function HomePage() {
  const theme = useTheme();
  const navigate = useNavigate();
  
  // Palette de couleurs élégante
  const darkBlue = '#00008B';
  const elegantRed = '#B22222'; // Rouge discret et sophistiqué
  
  // Fonctionnalités principales réduites à 4
  const features = [
    {
      title: 'Gestion des élèves',
      description: 'Suivi complet des dossiers',
      icon: <PeopleIcon fontSize="large" />
    },
    {
      title: 'Gestion enseignants',
      description: 'Organisation des emplois du temps',
      icon: <SchoolIcon fontSize="large" />
    },
    {
      title: 'Bulletins scolaires',
      description: 'Évaluations et notes',
      icon: <AssessmentIcon fontSize="large" />
    },
    {
      title: 'Suivi présences',
      description: 'Rapports d\'assiduité',
      icon: <EventNoteIcon fontSize="large" />
    }
  ];

  // Points forts résumés
  const highlights = [
    "Économisez jusqu'à 15 heures par semaine",
    "Interface adaptée pour tout le personnel",
    "Sécurité des données conforme RGPD"
  ];

  return (
    <Box sx={{ position: 'relative', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      {/* Contenu principal qui prend tout l'espace disponible */}
      <Box sx={{ flexGrow: 1 }}>
        {/* Section Hero */}
        <Hero />
        
        {/* Section Fonctionnalités */}
        <Box 
          sx={{ 
            py: 6,
            backgroundColor: 'background.default',
            width: '100%',
            position: 'relative',
            '&:before': {
              content: '""',
              position: 'absolute',
              top: 0,
              left: '50%',
              transform: 'translateX(-50%)',
              width: '60px',
              height: '3px',
              background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
              borderRadius: '2px'
            }
          }}
        >
          <Container maxWidth="lg">
            <Typography
              variant="h4"
              component="h2"
              fontWeight="bold"
              gutterBottom
              align="center"
              sx={{ 
                mb: 4,
                color: darkBlue,
                fontFamily: 'serif',
                mt: 2
              }}
            >
              Fonctionnalités principales
            </Typography>
            
            <Grid container spacing={4} justifyContent="center">
              {features.map((feature, index) => (
                <Grid item xs={12} sm={6} md={3} key={index}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 3,
                      height: 200,
                      borderRadius: 2,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      textAlign: 'center',
                      transition: 'transform 0.3s, box-shadow 0.3s, border-color 0.3s',
                      border: '1px solid',
                      borderColor: 'divider',
                      position: 'relative',
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '3px',
                        background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                        borderRadius: '2px 2px 0 0',
                        transition: 'height 0.3s ease'
                      },
                      '&:hover': {
                        transform: 'translateY(-6px)',
                        boxShadow: `0 10px 25px rgba(0,0,0,0.07), 0 0 0 1px ${elegantRed}20`,
                        borderColor: elegantRed
                      }
                    }}
                  >
                    <Box sx={{ 
                      color: darkBlue,
                      mb: 2,
                      fontSize: '2.5rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '60px'
                    }}>
                      {feature.icon}
                    </Box>
                    <Typography 
                      variant="h6" 
                      component="h3" 
                      fontWeight="bold" 
                      gutterBottom
                      sx={{
                        fontSize: '1.1rem',
                        height: '40px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {feature.title}
                    </Typography>
                    <Typography 
                      variant="body2" 
                      sx={{
                        color: darkBlue,
                        opacity: 0.8,
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.9rem'
                      }}
                    >
                      {feature.description}
                    </Typography>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Container>
        </Box>
        
        {/* Section Pourquoi nous choisir */}
        <Box 
          sx={{ 
            py: { xs: 5, md: 6 },
            bgcolor: 'grey.50',
            width: '100%',
            position: 'relative'
          }}
        >
          <Container maxWidth="md">
            <Box sx={{ textAlign: 'center', mb: 5 }}>
              <Typography 
                variant="h4" 
                component="h2" 
                gutterBottom 
                fontWeight="bold" 
                sx={{ color: darkBlue }}
              >
                Simplifiez votre gestion
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  color: '#222222',
                  fontSize: '1.1rem',
                  maxWidth: '700px', 
                  mx: 'auto',
                  mb: 4
                }}
              >
                Une interface intuitive pour centraliser toutes les données de votre établissement.
              </Typography>
            </Box>
            
            <Box sx={{ maxWidth: '550px', mx: 'auto' }}>
              {highlights.map((point, index) => (
                <Box 
                  key={index} 
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    mb: 2,
                    p: 2,
                    backgroundColor: 'white',
                    borderRadius: 1,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                    transition: 'transform 0.2s',
                    borderLeft: '3px solid transparent',
                    borderImage: `linear-gradient(180deg, ${elegantRed} 0%, ${darkBlue} 100%) 1`,
                    borderImageSlice: '0 0 0 1',
                    '&:hover': {
                      transform: 'translateX(10px)'
                    }
                  }}
                >
                  <CheckCircleIcon sx={{ 
                    color: darkBlue, 
                    mr: 2,
                    transition: 'color 0.3s'
                  }} />
                  <Typography>{point}</Typography>
                </Box>
              ))}
            </Box>
          </Container>
        </Box>
      </Box>
      <Footer />
    </Box>
  );
}

export default HomePage;