import React from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Card,
  CardContent
} from '@mui/material';
import { GraduationCap, Users, Settings, BarChart3, Shield, Clock } from 'lucide-react';
import Navbar from './layout/Navbar';
import Footer from './layout/Footer';

function AboutPage() {
  const darkBlue = '#00008B';
  const elegantRed = '#B22222';

  const features = [
    {
      icon: <Users size={32} />,
      title: 'Gestion complète',
      description: 'Gérez élèves, enseignants, classes et programmes en un seul endroit'
    },
    {
      icon: <BarChart3 size={32} />,
      title: 'Rapports détaillés',
      description: 'Suivez les performances avec des analyses approfondies'
    },
    {
      icon: <Shield size={32} />,
      title: 'Sécurité renforcée',
      description: 'Protection des données conforme aux normes RGPD'
    },
    {
      icon: <Clock size={32} />,
      title: 'Gain de temps',
      description: 'Automatisation des tâches répétitives et rapports instantanés'
    }
  ];

  const stats = [
    { number: '500+', label: 'Établissements utilisateurs' },
    { number: '50K+', label: 'Élèves gérés' },
    { number: '99.9%', label: 'Temps de fonctionnement' },
    { number: '24/7', label: 'Support technique' }
  ];

  return (
    <Box sx={{ width: '100%', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar />
      
      <Box sx={{ flexGrow: 1, width: '100%' }}>
        {/* Section Hero */}
        <Box
          sx={{
            width: '100%',
            background: `linear-gradient(135deg, ${darkBlue} 0%, ${elegantRed} 100%)`,
            color: 'white',
            py: { xs: 6, md: 8 },
            textAlign: 'center'
          }}
        >
          <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
              <GraduationCap size={60} />
            </Box>
            <Typography variant="h2" component="h1" gutterBottom fontWeight="bold" sx={{ fontSize: { xs: '2rem', md: '3.5rem' } }}>
              À propos d'EduSync
            </Typography>
            <Typography variant="h5" sx={{ maxWidth: '900px', mx: 'auto', opacity: 0.9, fontSize: { xs: '1.1rem', md: '1.5rem' } }}>
              La solution moderne de gestion scolaire qui simplifie l'administration éducative
            </Typography>
          </Container>
        </Box>

        {/* Section Mission */}
        <Box sx={{ width: '100%', py: { xs: 6, md: 8 } }}>
          <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 } }}>
            <Grid container spacing={6} alignItems="center">
              <Grid item xs={12} md={6}>
                <Typography variant="h3" component="h2" gutterBottom color={darkBlue} fontWeight="bold" sx={{ fontSize: { xs: '2rem', md: '2.5rem' } }}>
                  Notre Mission
                </Typography>
                <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.8 }}>
                  EduSync a été conçu pour révolutionner la gestion scolaire en offrant une plateforme
                  intuitive, complète et sécurisée. Notre objectif est de permettre aux établissements
                  scolaires de se concentrer sur l'essentiel : l'éducation.
                </Typography>
                <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.8 }}>
                  Nous croyons que la technologie doit simplifier, pas complexifier. C'est pourquoi
                  EduSync propose une interface moderne et une approche centrée sur l'utilisateur.
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <Paper
                  elevation={0}
                  sx={{
                    p: 4,
                    background: `linear-gradient(135deg, ${darkBlue}10 0%, ${elegantRed}10 100%)`,
                    borderRadius: 3,
                    height: '100%'
                  }}
                >
                  <Typography variant="h4" component="h3" gutterBottom color={darkBlue} fontWeight="bold" sx={{ fontSize: { xs: '1.5rem', md: '2rem' } }}>
                    Nos Valeurs
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <Shield color={darkBlue} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Sécurité et confidentialité"
                        secondary="Protection maximale des données sensibles"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Users color={darkBlue} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Simplicité d'usage"
                        secondary="Interface intuitive pour tous les utilisateurs"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Settings color={darkBlue} />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Innovation continue"
                        secondary="Évolution constante selon vos besoins"
                      />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
            </Grid>
          </Container>
        </Box>

        {/* Section Fonctionnalités */}
        <Box sx={{ width: '100%', py: { xs: 6, md: 8 }, bgcolor: 'grey.50' }}>
          <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 } }}>
            <Typography variant="h3" component="h2" textAlign="center" gutterBottom color={darkBlue} fontWeight="bold" sx={{ fontSize: { xs: '2rem', md: '2.5rem' } }}>
              Pourquoi choisir EduSync ?
            </Typography>
            <Typography variant="body1" textAlign="center" paragraph sx={{ mb: 6, fontSize: '1.1rem', maxWidth: '800px', mx: 'auto' }}>
              Une plateforme pensée pour répondre aux défis modernes de la gestion scolaire
            </Typography>
            
            <Grid container spacing={4}>
              {features.map((feature, index) => (
                <Grid item xs={12} sm={6} lg={3} key={index}>
                  <Card
                    elevation={0}
                    sx={{
                      height: '100%',
                      p: 3,
                      borderRadius: 3,
                      border: '1px solid',
                      borderColor: 'divider',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: `0 8px 25px rgba(0,0,0,0.1)`
                      }
                    }}
                  >
                    <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
                      <Box sx={{ color: darkBlue, mb: 2, textAlign: 'center' }}>
                        {feature.icon}
                      </Box>
                      <Typography variant="h5" component="h3" gutterBottom fontWeight="bold" textAlign="center">
                        {feature.title}
                      </Typography>
                      <Typography variant="body1" color="text.secondary" textAlign="center">
                        {feature.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Container>
        </Box>

        {/* Section Statistiques */}
        <Box sx={{ width: '100%', py: { xs: 6, md: 8 } }}>
          <Container maxWidth="xl" sx={{ px: { xs: 2, md: 4 } }}>
            <Typography variant="h3" component="h2" textAlign="center" gutterBottom color={darkBlue} fontWeight="bold" sx={{ fontSize: { xs: '2rem', md: '2.5rem' } }}>
              Ils nous font confiance
            </Typography>
            <Grid container spacing={4} sx={{ mt: 4 }}>
              {stats.map((stat, index) => (
                <Grid item xs={6} md={3} key={index}>
                  <Box textAlign="center">
                    <Typography 
                      variant="h2" 
                      component="div" 
                      fontWeight="bold"
                      sx={{ 
                        background: `linear-gradient(135deg, ${darkBlue} 0%, ${elegantRed} 100%)`,
                        backgroundClip: 'text',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        fontSize: { xs: '2.5rem', md: '3.5rem' }
                      }}
                    >
                      {stat.number}
                    </Typography>
                    <Typography variant="body1" color="text.secondary" fontWeight="medium">
                      {stat.label}
                    </Typography>
                  </Box>
                </Grid>
              ))}
            </Grid>
          </Container>
        </Box>
      </Box>

      <Footer />
    </Box>
  );
}

export default AboutPage; 