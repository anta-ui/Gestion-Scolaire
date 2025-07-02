import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Typography,
  Link,
  Divider,
  IconButton,
  useTheme
} from '@mui/material';
import FacebookIcon from '@mui/icons-material/Facebook';
import TwitterIcon from '@mui/icons-material/Twitter';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import InstagramIcon from '@mui/icons-material/Instagram';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import { GraduationCap } from 'lucide-react';

function Footer() {
  const theme = useTheme();
  const navigate = useNavigate();
  const currentYear = new Date().getFullYear();
  
  // Palette de couleurs élégante
  const darkBlue = '#00008B';
  const elegantRed = '#B22222';

  // Liens simplifiés en 2 catégories (Ressources supprimée)
  const linkCategories = [
    {
      title: "Navigation",
      links: [
        { name: "Accueil", path: "/" },
        { name: "À propos", path: "/about" },
        { name: "Services", path: "/services" },
        { name: "Contact", path: "/contact" }
      ]
    },
    {
      title: "Solutions",
      links: [
        { name: "Gestion des élèves", path: "/features/students" },
        { name: "Gestion des enseignants", path: "/features/teachers" },
        { name: "Bulletins scolaires", path: "/features/grades" },
        { name: "Suivi des présences", path: "/features/attendance" }
      ]
    }
  ];

  // Réseaux sociaux
  const socialLinks = [
    { icon: <FacebookIcon />, name: "Facebook", url: "#", color: darkBlue },
    { icon: <TwitterIcon />, name: "Twitter", url: "#", color: darkBlue },
    { icon: <LinkedInIcon />, name: "LinkedIn", url: "#", color: darkBlue },
    { icon: <InstagramIcon />, name: "Instagram", url: "#", color: darkBlue },
  ];

  return (
    <Box
      sx={{
        bgcolor: 'white',
        color: darkBlue,
        py: 5,
        borderTop: '1px solid',
        borderColor: 'divider',
        boxShadow: '0px -2px 10px rgba(0,0,0,0.05)',
        position: 'relative',
        '&:before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '100px',
          height: '3px',
          background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 50%, ${elegantRed} 100%)`,
          borderRadius: '0 0 2px 2px'
        }
      }}
      component="footer"
    >
      <Container maxWidth="xl">
        <Grid container spacing={4} justifyContent="space-between">
          {/* Logo et information de contact */}
          <Grid item xs={12} md={4} lg={3}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '40%',
                    background: `linear-gradient(135deg, ${darkBlue} 0%, ${elegantRed} 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: `0 4px 12px rgba(0, 0, 139, 0.3), 0 2px 6px ${elegantRed}20`,
                    position: 'relative',
                    '&:after': {
                      content: '""',
                      position: 'absolute',
                      inset: '2px',
                      borderRadius: '30%',
                      background: `linear-gradient(135deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                      opacity: 0,
                      transition: 'opacity 0.3s ease'
                    },
                    '&:hover:after': {
                      opacity: 0.1
                    }
                  }}
                >
                  <GraduationCap size={30} color="white" style={{ zIndex: 1 }} />
                </Box>
                <Typography
                  variant="h5"
                  noWrap
                  
                  sx={{
                    mr: 4,
                    display: { xs: 'none', md: 'flex' },
                    fontFamily: '"Inter", sans-serif',
                    fontWeight: 700,
                    letterSpacing: '.2rem',
                    color: darkBlue,
                    textDecoration: 'none',
                  }}
                >
                  EDUSYNC
                </Typography>
              </Box>
            <Typography variant="body2" sx={{ color: darkBlue, opacity: 0.85, mb: 2, maxWidth: 300 }}>
              Simplifiez la gestion scolaire de votre établissement avec notre solution complète.
            </Typography>
            
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              mb: 1,
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'translateX(5px)'
              }
            }}>
              <EmailIcon sx={{ fontSize: 18, mr: 1.5, color: darkBlue }} />
              <Typography variant="body2" sx={{ color: darkBlue }}>contact@edusync.com</Typography>
            </Box>
            
            <Box sx={{ 
              display: 'flex', 
              alignItems: 'center',
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'translateX(5px)'
              }
            }}>
              <PhoneIcon sx={{ fontSize: 18, mr: 1.5, color: darkBlue }} />
              <Typography variant="body2" sx={{ color: darkBlue }}>+33 1 23 45 67 89</Typography>
            </Box>
          </Grid>

          {/* 2 colonnes de liens (Navigation et Solutions) */}
          {linkCategories.map((category, i) => (
            <Grid item xs={12} sm={6} md={3} lg={3} key={i}>
              <Typography variant="subtitle1" fontWeight="bold" sx={{ 
                mb: 2, 
                color: darkBlue,
                position: 'relative',
                '&:after': {
                  content: '""',
                  position: 'absolute',
                  bottom: '-4px',
                  left: 0,
                  width: '30px',
                  height: '2px',
                  background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                  borderRadius: '1px'
                }
              }}>
                {category.title}
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2 }}>
                {category.links.map((link, j) => (
                  <Link 
                    key={j} 
                    component="button"
                    onClick={() => navigate(link.path)}
                    sx={{ 
                      color: darkBlue,
                      opacity: 0.8,
                      textDecoration: 'none',
                      fontSize: '0.9rem',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      position: 'relative',
                      transition: 'all 0.2s ease',
                      '&:before': {
                        content: '""',
                        position: 'absolute',
                        left: '-10px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        width: '0px',
                        height: '2px',
                        background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                        transition: 'width 0.3s ease'
                      },
                      '&:hover': { 
                        opacity: 1,
                        textDecoration: 'underline',
                        transform: 'translateX(5px)',
                        '&:before': {
                          width: '6px'
                        }
                      }
                    }}
                  >
                    {link.name}
                  </Link>
                ))}
              </Box>
            </Grid>
          ))}

          {/* Réseaux sociaux à la place de Ressources */}
          <Grid item xs={12} sm={6} md={3} lg={3}>
            <Typography variant="subtitle1" fontWeight="bold" sx={{ 
              mb: 2, 
              color: darkBlue,
              position: 'relative',
              '&:after': {
                content: '""',
                position: 'absolute',
                bottom: '-4px',
                left: 0,
                width: '30px',
                height: '2px',
                background: `linear-gradient(90deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                borderRadius: '1px'
              }
            }}>
              Suivez-nous
            </Typography>
            
            {/* Liste des réseaux sociaux avec texte */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.2 }}>
              {socialLinks.map((social, i) => (
                <Link
                  key={i}
                  href={social.url}
                  underline="none"
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    color: darkBlue,
                    opacity: 0.8,
                    transition: 'all 0.2s ease',
                    '&:hover': { 
                      opacity: 1,
                      transform: 'translateX(5px)'
                    }
                  }}
                >
                  <Box 
                    sx={{ 
                      mr: 1.5,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 30, 
                      height: 30,
                      borderRadius: '50%',
                      backgroundColor: social.color,
                      color: 'white',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'scale(1.1)',
                        boxShadow: `0 4px 8px ${social.color}40`
                      }
                    }}
                  >
                    {social.icon}
                  </Box>
                  <Typography variant="body2">{social.name}</Typography>
                </Link>
              ))}
            </Box>
          </Grid>
        </Grid>

        {/* Séparateur avec gradient */}
        <Divider sx={{ 
          my: 4, 
          background: `linear-gradient(90deg, transparent 0%, ${elegantRed} 20%, ${darkBlue} 50%, ${elegantRed} 80%, transparent 100%)`,
          height: '1px',
          border: 'none'
        }} />

        {/* Copyright */}
        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="body2" sx={{ color: darkBlue, opacity: 0.7 }}>
            © {currentYear} EduSync. Tous droits réservés.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default Footer;