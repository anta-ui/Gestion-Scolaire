import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Collapse,
  Box,
  Typography,
  Divider,
  IconButton,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  School as SchoolIcon,
  People as PeopleIcon,
  AssignmentTurnedIn as ExamIcon,
  EventNote as AttendanceIcon,
  FamilyRestroom as ParentIcon,
  PersonAdd as AdmissionIcon,
  AccountBalance as AcademicIcon,
  Settings as ConfigIcon,
  ExpandLess,
  ExpandMore,
  LibraryBooks as LibraryIcon,
  Menu as MenuIcon,
  Logout as LogoutIcon,
  Assessment as BulletinIcon,
  Quiz as EvaluationIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const menuItems = [
  {
    id: 'dashboard',
    label: 'Tableau de bord',
    icon: <DashboardIcon />,
    path: '/dashboard'
  },
  {
    id: 'students',
    label: 'Gestion de l\'école',
    icon: <PeopleIcon />,
    children: [
      { id: 'student-list', label: 'Étudiants', path: '/students' },
      { id: 'students-parents', label: 'Parents', path: '/students-parents' },
      
      { id: 'classes', label: 'Promotions', path: '/batches' },
      { id: 'courses', label: 'Cours', path: '/courses' },
      { id: 'subjects', label: 'Matières', path: '/subjects' },
      { id: 'teachers',label: 'Enseignants',path: '/teachers'},
      { id: 'exams',label: 'Evaluations',path: '/exams'},
      { id: 'bulletins', label: 'Bulletins', path: '/bulletins' },
      {id:'timetables',label:'Emplois du temps',path:'/timetables'},
      { id: 'admissions-management', label: 'Admissions', path: '/admissions' },
      { id: 'fees-management', label: 'Frais', path: '/fees' },
      
    ]
  },
  
  {
    id: 'attendance',
    label: 'Présences',
    icon: <AttendanceIcon />,
    children: [
      { id: 'attendance-dashboard', label: 'Tableau de bord', path: '/attendance/dashboard' },
      { id: 'session-manager', label: 'Gestion des Sessions', path: '/sessions/manager' },
      { id: 'attendance-register', label: 'Registre de présence', path: '/attendance/register' },
      
      
    ]
  },
      
  {
    id: 'library',
    label: 'Bibliothèque',
    icon: <LibraryIcon />,
    children: [
      { id: 'library-dashboard', label: 'Tableau de bord', path: '/library' },
      { id: 'library-books', label: 'Gestion des Livres', path: '/library/books' },
      { id: 'library-authors', label: 'Auteurs', path: '/library/authors' },
      { id: 'library-categories', label: 'Catégories', path: '/library/categories' },
      { id: 'library-borrowings', label: 'Emprunts', path: '/library/borrowings' },
      
    ]
  },
  
  
  
  
  
  
  
];

const Sidebar = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState({});

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenuClick = (menuId) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuId]: !prev[menuId]
    }));
  };

  const handleNavigate = (path) => {
    navigate(path);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const renderMenuItem = (item) => {
    const isExpanded = expandedMenus[item.id];
    const isSelected = location.pathname === item.path;

    if (item.children) {
      return (
        <React.Fragment key={item.id}>
          <ListItem disablePadding>
            <ListItemButton
              onClick={() => handleMenuClick(item.id)}
              sx={{
                pl: 2,
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 139, 0.08)',
                }
              }}
            >
              <ListItemIcon sx={{ color: '#00008B' }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} />
              {isExpanded ? <ExpandLess /> : <ExpandMore />}
            </ListItemButton>
          </ListItem>
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children.map((child) => (
                <ListItemButton
                  key={child.id}
                  sx={{
                    pl: 4,
                    backgroundColor: location.pathname === child.path ? 'rgba(0, 0, 139, 0.08)' : 'transparent',
                    '&:hover': {
                      backgroundColor: 'rgba(0, 0, 139, 0.12)',
                    }
                  }}
                  onClick={() => handleNavigate(child.path)}
                >
                  <ListItemText primary={child.label} />
                </ListItemButton>
              ))}
            </List>
          </Collapse>
        </React.Fragment>
      );
    }

    return (
      <ListItem key={item.id} disablePadding>
        <ListItemButton
          onClick={() => handleNavigate(item.path)}
          sx={{
            pl: 2,
            backgroundColor: isSelected ? 'rgba(0, 0, 139, 0.08)' : 'transparent',
            '&:hover': {
              backgroundColor: 'rgba(0, 0, 139, 0.12)',
            }
          }}
        >
          <ListItemIcon sx={{ color: '#00008B' }}>
            {item.icon}
          </ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItemButton>
      </ListItem>
    );
  };

  const drawer = (
    <>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SchoolIcon sx={{ color: '#00008B' }} />
          <Typography variant="h6" sx={{ color: '#00008B' }}>
            EDUSYNC
          </Typography>
        </Box>
        {isMobile && (
          <IconButton onClick={handleDrawerToggle}>
            <MenuIcon />
          </IconButton>
        )}
      </Box>
      <Divider />
      <List component="nav" sx={{ flexGrow: 1 }}>
        {menuItems.map(renderMenuItem)}
      </List>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon sx={{ color: '#00008B' }} />
            </ListItemIcon>
            <ListItemText primary="Déconnexion" />
          </ListItemButton>
        </ListItem>
      </List>
    </>
  );

  return (
    <>
      {isMobile && (
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{
            position: 'fixed',
            top: 16,
            left: 16,
            zIndex: theme.zIndex.drawer + 2,
            backgroundColor: 'white',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            '&:hover': {
              backgroundColor: 'rgba(255,255,255,0.9)',
            },
          }}
        >
          <MenuIcon />
        </IconButton>
      )}
      <Box
        component="nav"
        sx={{
          width: { md: 280 },
          flexShrink: { md: 0 },
        }}
      >
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{
              keepMounted: true, // Better open performance on mobile
            }}
            sx={{
              display: { xs: 'block', md: 'none' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: 280,
              },
            }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', md: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: 280,
                backgroundColor: '#ffffff',
                borderRight: '1px solid rgba(0, 0, 0, 0.12)',
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        )}
      </Box>
    </>
  );
};

export default Sidebar; 