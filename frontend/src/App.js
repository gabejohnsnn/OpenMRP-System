// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useParams } from 'react-router-dom';
import { 
  CssBaseline, AppBar, Toolbar, Typography, Container, Box,
  Drawer, List, ListItem, ListItemIcon, ListItemText, Divider,
  Collapse
} from '@mui/material';
import InventoryIcon from '@mui/icons-material/Inventory';
import ListAltIcon from '@mui/icons-material/ListAlt';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import FactoryIcon from '@mui/icons-material/Factory';
import EventNoteIcon from '@mui/icons-material/EventNote';
import CalculateIcon from '@mui/icons-material/Calculate';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';

const drawerWidth = 240;

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

// Separate component to use routing hooks
function AppContent() {
  const location = useLocation();
  const [inventoryOpen, setInventoryOpen] = React.useState(true);
  const [productionOpen, setProductionOpen] = React.useState(true);
  
  const handleInventoryClick = () => {
    setInventoryOpen(!inventoryOpen);
  };
  
  const handleProductionClick = () => {
    setProductionOpen(!productionOpen);
  };
  
  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            OpenMRP
          </Typography>
        </Toolbar>
      </AppBar>
      
      {/* Side Navigation */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar /> {/* This creates space for the AppBar */}
        <Box sx={{ overflow: 'auto' }}>
          <List>
            <ListItem 
              button 
              component={Link} 
              to="/"
              selected={location.pathname === '/'}
            >
              <ListItemIcon><DashboardIcon /></ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItem>
            
            {/* Inventory with nested menu */}
            <ListItem button onClick={handleInventoryClick}>
              <ListItemIcon><InventoryIcon /></ListItemIcon>
              <ListItemText primary="Inventory" />
              {inventoryOpen ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={inventoryOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItem 
                  button 
                  component={Link} 
                  to="/inventory"
                  selected={location.pathname === '/inventory'}
                  sx={{ pl: 4 }}
                >
                  <ListItemText primary="Items" />
                </ListItem>
                <ListItem 
                  button 
                  component={Link} 
                  to="/inventory/transactions"
                  selected={location.pathname.startsWith('/inventory/transactions')}
                  sx={{ pl: 4 }}
                >
                  <ListItemIcon><SwapHorizIcon /></ListItemIcon>
                  <ListItemText primary="Transactions" />
                </ListItem>
              </List>
            </Collapse>
            
            <ListItem 
              button 
              component={Link} 
              to="/bom"
              selected={location.pathname.startsWith('/bom')}
            >
              <ListItemIcon><ListAltIcon /></ListItemIcon>
              <ListItemText primary="Bill of Materials" />
            </ListItem>
            
            {/* Production Planning with nested menu */}
            <ListItem button onClick={handleProductionClick}>
              <ListItemIcon><FactoryIcon /></ListItemIcon>
              <ListItemText primary="Production" />
              {productionOpen ? <ExpandLess /> : <ExpandMore />}
            </ListItem>
            <Collapse in={productionOpen} timeout="auto" unmountOnExit>
              <List component="div" disablePadding>
                <ListItem 
                  button 
                  component={Link} 
                  to="/production/mps"
                  selected={location.pathname.startsWith('/production/mps')}
                  sx={{ pl: 4 }}
                >
                  <ListItemIcon><EventNoteIcon /></ListItemIcon>
                  <ListItemText primary="Master Schedule" />
                </ListItem>
                <ListItem 
                  button 
                  component={Link} 
                  to="/production/mrp"
                  selected={location.pathname.startsWith('/production/mrp')}
                  sx={{ pl: 4 }}
                >
                  <ListItemIcon><CalculateIcon /></ListItemIcon>
                  <ListItemText primary="Material Planning" />
                </ListItem>
                <ListItem 
                  button 
                  component={Link} 
                  to="/production/orders"
                  selected={location.pathname.startsWith('/production/orders')}
                  sx={{ pl: 4 }}
                >
                  <ListItemText primary="Production Orders" />
                </ListItem>
              </List>
            </Collapse>
          </List>
          <Divider />
          <List>
            <ListItem button component={Link} to="/settings">
              <ListItemIcon><SettingsIcon /></ListItemIcon>
              <ListItemText primary="Settings" />
            </ListItem>
          </List>
        </Box>
      </Drawer>
      
      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* This creates space for the AppBar */}
        <Container maxWidth="xl">
          <Routes>
            {/* Dashboard */}
            <Route path="/" element={<Dashboard />} />
            
            {/* Inventory */}
            <Route path="/inventory" element={<div>Inventory Management</div>} />
            <Route path="/inventory/transactions" element={<div>Inventory Transactions</div>} />
            
            {/* BOM */}
            <Route path="/bom" element={<div>Bill of Materials</div>} />
            
            {/* Production Planning */}
            <Route path="/production/mps" element={<div>Master Production Schedule</div>} />
            <Route path="/production/mrp" element={<div>Material Requirements Planning</div>} />
            <Route path="/production/orders" element={<div>Production Orders</div>} />
            
            {/* Settings */}
            <Route path="/settings" element={<div>Settings</div>} />
          </Routes>
        </Container>
      </Box>
    </Box>
  );
}

// Simple Dashboard placeholder
function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Typography paragraph>
        Welcome to OpenMRP - an open-source Manufacturing Resource Planning system.
      </Typography>
      <Typography paragraph>
        The system includes these core modules:
      </Typography>
      <ul>
        <li>
          <Typography>
            <strong>Inventory Management</strong> - track inventory items and their quantities
          </Typography>
        </li>
        <li>
          <Typography>
            <strong>Inventory Transactions</strong> - record receipts, issues, transfers, and adjustments
          </Typography>
        </li>
        <li>
          <Typography>
            <strong>Bill of Materials</strong> - define product structures with components and quantities
          </Typography>
        </li>
        <li>
          <Typography>
            <strong>Production Planning</strong>:
            <ul>
              <li>Master Production Schedule (MPS) - plan what to produce and when</li>
              <li>Material Requirements Planning (MRP) - calculate material needs</li>
              <li>Production Orders - manage shop floor execution</li>
            </ul>
          </Typography>
        </li>
      </ul>
    </Box>
  );
}

export default App;
