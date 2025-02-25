// frontend/src/components/InventoryList.js
import React, { useState, useEffect } from 'react';
import { 
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Button, TextField, Box, Typography, CircularProgress,
  IconButton, Alert
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import * as api from '../services/api';

const InventoryList = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchItems = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getInventoryItems(searchTerm);
      setItems(data);
    } catch (err) {
      setError('Failed to load inventory items');
      console.error('Error fetching inventory items:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await api.deleteInventoryItem(id);
        setItems(items.filter(item => item.id !== id));
      } catch (err) {
        setError('Failed to delete item');
        console.error('Error deleting item:', err);
      }
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Inventory Items</Typography>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          // onClick={() => /* Navigate to create form */}
        >
          Add New Item
        </Button>
      </Box>

      <Box sx={{ display: 'flex', mb: 2 }}>
        <TextField
          label="Search Items"
          variant="outlined"
          size="small"
          value={searchTerm}
          onChange={handleSearchChange}
          sx={{ mr: 1, flexGrow: 1 }}
        />
        <Button 
          variant="contained" 
          onClick={fetchItems}
        >
          Search
        </Button>
        <IconButton onClick={fetchItems} sx={{ ml: 1 }}>
          <RefreshIcon />
        </IconButton>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }} aria-label="inventory table">
            <TableHead>
              <TableRow>
                <TableCell>Item Code</TableCell>
                <TableCell>Name</TableCell>
                <TableCell>Unit of Measure</TableCell>
                <TableCell align="right">Quantity On Hand</TableCell>
                <TableCell align="right">Unit Cost</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.length > 0 ? (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.item_code}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.uom}</TableCell>
                    <TableCell align="right">{item.quantity_on_hand}</TableCell>
                    <TableCell align="right">${item.unit_cost.toFixed(2)}</TableCell>
                    <TableCell>
                      <IconButton size="small" 
                        // onClick={() => /* Navigate to edit form */}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(item.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">No items found</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default InventoryList;
