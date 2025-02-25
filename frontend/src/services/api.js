// frontend/src/services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Inventory API functions
export const getInventoryItems = async (search = '', skip = 0, limit = 100) => {
  try {
    const response = await api.get('inventory/items/', { 
      params: { search, skip, limit } 
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching inventory items:', error);
    throw error;
  }
};

export const getInventoryItem = async (id) => {
  try {
    const response = await api.get(`inventory/items/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching inventory item ${id}:`, error);
    throw error;
  }
};

export const createInventoryItem = async (itemData) => {
  try {
    const response = await api.post('inventory/items/', itemData);
    return response.data;
  } catch (error) {
    console.error('Error creating inventory item:', error);
    throw error;
  }
};

export const updateInventoryItem = async (id, itemData) => {
  try {
    const response = await api.put(`inventory/items/${id}`, itemData);
    return response.data;
  } catch (error) {
    console.error(`Error updating inventory item ${id}:`, error);
    throw error;
  }
};

export const deleteInventoryItem = async (id) => {
  try {
    const response = await api.delete(`inventory/items/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting inventory item ${id}:`, error);
    throw error;
  }
};

// Category API functions
export const getCategories = async () => {
  try {
    const response = await api.get('inventory/categories/');
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

export const createCategory = async (categoryData) => {
  try {
    const response = await api.post('inventory/categories/', categoryData);
    return response.data;
  } catch (error) {
    console.error('Error creating category:', error);
    throw error;
  }
};

export default api;
