import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Button,
  Container,
  Menu,
  MenuItem,
  useScrollTrigger,
  Slide,
  Fade,
  Avatar,
  Tooltip
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SchoolRoundedIcon from '@mui/icons-material/SchoolRounded';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAuth } from '../../contexts/AuthContext';
import { GraduationCap } from 'lucide-react';
// Importer les constantes pour la navigation standardisée
import { ROUTES, ENTITY_DISPLAY_NAMES, EDUCATION_LEVEL_NAMES } from '../../utils/constants';

// Fonction pour masquer la navbar lors du défilement vers le bas
function HideOnScroll(props) {
  const { children } = props;
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

function Navbar() {
  const [anchorElNav, setAnchorElNav] = useState(null);
  const [anchorElFeatures, setAnchorElFeatures] = useState(null);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();
  
  // Palette de couleurs élégante
  const darkBlue = '#00008B';
  const elegantRed = '#B22222';

  // Ajouter un effet de changement de couleur au défilement
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 50) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleOpenNavMenu = (event) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleOpenFeaturesMenu = (event) => {
    setAnchorElFeatures(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleCloseFeaturesMenu = () => {
    setAnchorElFeatures(null);
  };

  // Liste des pages principales utilisant les constantes de routes
  const pages = [
    { name: 'Accueil', path: ROUTES.HOME },
    { name: 'À propos', path: '/about'},
    { name: 'Formulaire publique', path: '/formulaire-publique' },
    { name: 'Contact', path: '/contact' },

  ];

  // Liste des fonctionnalités pour le sous-menu utilisant les constantes et les noms standardisés
  const features = [
    { name: `Gestion des ${ENTITY_DISPLAY_NAMES.STUDENT}s`, path: '/features/students' },
    { name: `Gestion des ${ENTITY_DISPLAY_NAMES.TEACHER}s`, path: '/features/teachers' },
    { name: `Gestion des ${ENTITY_DISPLAY_NAMES.BATCH}s`, path: '/features/classes' },
    { name: 'Notes et évaluations', path: '/features/grades' },
    { name: 'Présences', path: '/features/attendance' },
  ];

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <HideOnScroll>
      <AppBar 
        position="sticky" 
        sx={{ 
          bgcolor: 'white',
          transition: 'all 0.3s ease',
          backdropFilter: isScrolled ? 'blur(8px)' : 'none',
          color: darkBlue,
        }}
        elevation={isScrolled ? 4 : 2}
      >
        <Container maxWidth="xl">
          <Toolbar disableGutters sx={{ py: 1 }}>
            {/* Logo et titre pour les écrans larges */}
            <Fade in={true} timeout={1000}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  sx={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    background: `linear-gradient(135deg, ${darkBlue} 0%, ${elegantRed} 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: `0 4px 12px rgba(0, 0, 139, 0.3), 0 2px 6px ${elegantRed}20`,
                    position: 'relative',
                    '&:before': {
                      content: '""',
                      position: 'absolute',
                      inset: '2px',
                      borderRadius: '50%',
                      background: `linear-gradient(135deg, ${elegantRed} 0%, ${darkBlue} 100%)`,
                      opacity: 0,
                      transition: 'opacity 0.3s ease'
                    },
                    '&:hover:before': {
                      opacity: 0.1
                    }
                  }}
                >
                  <GraduationCap size={30} color="white" style={{ zIndex: 1 }} />
                </Box>
                <Typography
                  variant="h5"
                  noWrap
                  component={RouterLink}
                  to="/"
                  sx={{
                    mr: 4,
                    display: { xs: 'none', md: 'flex' },
                    fontFamily: '"Inter", sans-serif',
                    fontWeight: 700,
                    letterSpacing: '.2rem',
                    color: darkBlue,
                    textDecoration: 'none',
                    position: 'relative',
                    '&:after': {
                      content: '""',
                      position: 'absolute',
                      bottom: '-2px',
                      left: 0,
                      width: '0%',
                      height: '2px',
                      background: `linear-gradient(90deg, ${darkBlue}, ${elegantRed})`,
                      transition: 'width 0.3s ease'
                    },
                    '&:hover:after': {
                      width: '100%'
                    }
                  }}
                >
                  EDUSYNC
                </Typography>
              </Box>
            </Fade>

            {/* Menu hamburger pour mobile */}
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <IconButton
                size="large"
                aria-label="menu"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleOpenNavMenu}
                sx={{ 
                  color: darkBlue,
                  position: 'relative',
                  '&:before': {
                    content: '""',
                    position: 'absolute',
                    inset: '4px',
                    borderRadius: '50%',
                    border: `1px solid transparent`,
                    background: `linear-gradient(45deg, ${elegantRed}20, transparent) border-box`,
                    mask: 'linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0)',
                    maskComposite: 'exclude',
                    opacity: 0,
                    transition: 'opacity 0.3s ease'
                  },
                  '&:hover': { 
                    backgroundColor: `${darkBlue}10`,
                    transform: 'scale(1.05)',
                    '&:before': {
                      opacity: 1
                    }
                  },
                  transition: 'all 0.2s ease' 
                }}
              >
                <MenuIcon />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorElNav}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
                open={Boolean(anchorElNav)}
                onClose={handleCloseNavMenu}
                sx={{
                  display: { xs: 'block', md: 'none' },
                  '& .MuiPaper-root': {
                    borderRadius: 2,
                    mt: 1.5,
                    boxShadow: '0px 8px 16px rgba(0,0,0,0.1)',
                  },
                }}
              >
                {pages.map((page) => (
                  <MenuItem 
                    key={page.name} 
                    onClick={handleCloseNavMenu}
                    component={RouterLink}
                    to={page.path}
                    selected={location.pathname === page.path}
                    sx={{
                      borderLeft: location.pathname === page.path ? 3 : 0,
                      borderColor: darkBlue,
                      backgroundColor: location.pathname === page.path ? `${darkBlue}10` : 'transparent',
                      '&:hover': {
                        backgroundColor: `${darkBlue}10`,
                      },
                      transition: 'all 0.2s ease',
                      px: 3,
                      py: 1.5,
                    }}
                  >
                    <Typography textAlign="center" sx={{ color: darkBlue }}>
                      {page.name}
                    </Typography>
                  </MenuItem>
                ))}
              </Menu>
            </Box>

            {/* Logo et titre pour mobile */}
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' }, alignItems: 'center' }}>
              <Box
                sx={{
                  width: 45,
                  height: 45,
                  borderRadius: '50%',
                  backgroundColor: darkBlue,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mr: 1,
                  boxShadow: '0 4px 12px rgba(0, 0, 139, 0.3)'
                }}
              >
                <GraduationCap size={25} color="white" />
              </Box>
              <Typography
                variant="h6"
                noWrap
                component={RouterLink}
                to="/"
                sx={{
                  fontFamily: '"Inter", sans-serif',
                  fontWeight: 700,
                  letterSpacing: '.1rem',
                  color: darkBlue,
                  textDecoration: 'none',
                }}
              >
                EDUSYNC
              </Typography>
            </Box>

            {/* Navigation pour les écrans larges */}
            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, ml: 2 }}>
              {pages.map((page) => (
                page.hasSubmenu ? (
                  <Box key={page.name} sx={{ position: 'relative' }}>
                    <Button
                      onClick={handleOpenFeaturesMenu}
                      sx={{
                        my: 2,
                        mx: 1,
                        color: darkBlue,
                        display: 'flex',
                        alignItems: 'center',
                        '&:hover': {
                          backgroundColor: `${darkBlue}10`,
                        },
                        backgroundColor: location.pathname.startsWith(page.path) ? `${darkBlue}10` : 'transparent',
                        borderRadius: 2,
                        px: 2,
                      }}
                      endIcon={<KeyboardArrowDownIcon />}
                    >
                      {page.name}
                    </Button>
                    <Menu
                      id="features-menu"
                      anchorEl={anchorElFeatures}
                      open={Boolean(anchorElFeatures)}
                      onClose={handleCloseFeaturesMenu}
                      sx={{
                        '& .MuiPaper-root': {
                          borderRadius: 2,
                          mt: 1,
                          minWidth: 220,
                          boxShadow: '0px 8px 16px rgba(0,0,0,0.1)',
                        },
                      }}
                    >
                      {features.map((feature) => (
                        <MenuItem
                          key={feature.name}
                          onClick={handleCloseFeaturesMenu}
                          component={RouterLink}
                          to={feature.path}
                          sx={{
                            px: 2.5,
                            py: 1.5,
                            '&:hover': {
                              backgroundColor: `${darkBlue}10`,
                            }
                          }}
                        >
                          <Typography variant="body1" sx={{ color: darkBlue }}>
                            {feature.name}
                          </Typography>
                        </MenuItem>
                      ))}
                    </Menu>
                  </Box>
                ) : (
                  <Button
                    key={page.name}
                    component={RouterLink}
                    to={page.path}
                    sx={{
                      my: 2,
                      mx: 1,
                      color: darkBlue,
                      display: 'block',
                      '&:hover': {
                        backgroundColor: `${darkBlue}10`,
                      },
                      backgroundColor: location.pathname === page.path ? `${darkBlue}10` : 'transparent',
                      borderRadius: 2,
                      px: 2,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    {page.name}
                  </Button>
                )
              ))}
            </Box>

            {/* Boutons de connexion et actualisation */}
            <Box sx={{ flexGrow: 0, display: 'flex', alignItems: 'center' }}>
              <Tooltip title="Actualiser les données">
                <IconButton
                  onClick={handleRefresh}
                  sx={{
                    mr: 2,
                    color: darkBlue,
                    '&:hover': {
                      backgroundColor: `${darkBlue}10`,
                    }
                  }}
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              <Button 
                variant="outlined"
                component={RouterLink}
                to="/parent"
                sx={{
                  ml: 2,
                  color: darkBlue,
                  background: 'white',
                  border: '2px solid',
                  borderImage: `linear-gradient(90deg, ${darkBlue} 0%, ${elegantRed} 100%) 1`,
                  borderRadius: '4px',
                  position: 'relative',
                  fontWeight: 'bold',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 184, 0.04)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(0, 0, 139, 0.2)'
                  }
                }}
              >
                Portail Parent
              </Button>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>
    </HideOnScroll>
  );
}

export default Navbar;