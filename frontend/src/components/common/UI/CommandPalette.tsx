/**
 * TASK 14: Advanced User Interface Enhancements
 * 
 * CommandPalette - Global search and command interface
 * 
 * Features:
 * - Global search across all system entities
 * - Quick navigation to pages and features
 * - Keyboard shortcuts execution
 * - Recent searches and commands
 * - Fuzzy search with highlighting
 * - Category-based organization
 * - Real-time suggestions
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Dialog,
  DialogContent,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Chip,
  Divider,
  InputAdornment,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Search as SearchIcon,
  Dashboard,
  AccountBalance,
  Analytics,
  Person,
  Settings,
  Help,
  Description,
  TrendingUp,
  Security,
  Keyboard,
  NavigateNext,
  History,
  Star,
} from '@mui/icons-material';
import { Command } from 'cmdk';
import { useNavigate } from 'react-router-dom';
import { useHotkeys } from 'react-hotkeys-hook';
import { useLocalStorage } from 'react-use';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeVariants, staggerContainer, staggerItem } from '../Animations/variants';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  category: string;
  icon: React.ReactNode;
  action: () => void;
  keywords: string[];
  priority?: number;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

const CommandPalette: React.FC<CommandPaletteProps> = ({ open, onClose }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useLocalStorage<string[]>('recent-commands', []);

  // Define all available commands
  const commands: CommandItem[] = useMemo(() => [
    // Navigation
    {
      id: 'nav-dashboard',
      title: 'Dashboard',
      subtitle: 'Go to main dashboard',
      category: 'Navigation',
      icon: <Dashboard />,
      action: () => navigate('/dashboard'),
      keywords: ['dashboard', 'home', 'main'],
      priority: 10,
    },
    {
      id: 'nav-assets',
      title: 'Asset Management',
      subtitle: 'View and manage assets',
      category: 'Navigation',
      icon: <AccountBalance />,
      action: () => navigate('/assets'),
      keywords: ['assets', 'portfolio', 'investments'],
      priority: 9,
    },
    {
      id: 'nav-analytics',
      title: 'Financial Analytics',
      subtitle: 'Advanced analysis and reporting',
      category: 'Navigation',
      icon: <Analytics />,
      action: () => navigate('/analytics'),
      keywords: ['analytics', 'reports', 'analysis', 'financial'],
      priority: 8,
    },
    {
      id: 'nav-portfolio',
      title: 'Portfolio Manager',
      subtitle: 'Portfolio management dashboard',
      category: 'Navigation',
      icon: <TrendingUp />,
      action: () => navigate('/portfolio'),
      keywords: ['portfolio', 'manager', 'performance'],
      priority: 8,
    },

    // System Actions
    {
      id: 'action-settings',
      title: 'Settings',
      subtitle: 'Application settings',
      category: 'System',
      icon: <Settings />,
      action: () => navigate('/settings'),
      keywords: ['settings', 'preferences', 'config'],
      priority: 6,
    },
    {
      id: 'action-profile',
      title: 'User Profile',
      subtitle: 'Manage your profile',
      category: 'System',
      icon: <Person />,
      action: () => navigate('/profile'),
      keywords: ['profile', 'account', 'user'],
      priority: 5,
    },
    {
      id: 'action-help',
      title: 'Help & Documentation',
      subtitle: 'Get help and view documentation',
      category: 'System',
      icon: <Help />,
      action: () => navigate('/help'),
      keywords: ['help', 'documentation', 'support', 'guide'],
      priority: 4,
    },

    // Quick Actions
    {
      id: 'quick-create-asset',
      title: 'Create New Asset',
      subtitle: 'Add a new asset to the portfolio',
      category: 'Quick Actions',
      icon: <AccountBalance />,
      action: () => navigate('/assets/create'),
      keywords: ['create', 'new', 'asset', 'add'],
      priority: 7,
    },
    {
      id: 'quick-generate-report',
      title: 'Generate Report',
      subtitle: 'Create a new performance report',
      category: 'Quick Actions',
      icon: <Description />,
      action: () => navigate('/reports/generate'),
      keywords: ['report', 'generate', 'export', 'document'],
      priority: 6,
    },

    // Features
    {
      id: 'feature-waterfall',
      title: 'Waterfall Analysis',
      subtitle: 'Analyze CLO payment waterfalls',
      category: 'Features',
      icon: <Analytics />,
      action: () => navigate('/analytics/waterfall'),
      keywords: ['waterfall', 'payment', 'clo', 'analysis'],
      priority: 7,
    },
    {
      id: 'feature-correlation',
      title: 'Correlation Analysis',
      subtitle: 'Asset correlation matrix and analysis',
      category: 'Features',
      icon: <Security />,
      action: () => navigate('/analytics/correlation'),
      keywords: ['correlation', 'matrix', 'risk', 'analysis'],
      priority: 7,
    },

    // Keyboard Shortcuts
    {
      id: 'shortcut-search',
      title: 'Search (Ctrl+K)',
      subtitle: 'Open command palette',
      category: 'Shortcuts',
      icon: <Keyboard />,
      action: () => {},
      keywords: ['search', 'command', 'palette', 'shortcut'],
      priority: 3,
    },
  ], [navigate]);

  // Filter commands based on search query
  const filteredCommands = useMemo(() => {
    if (!query) {
      // Show recent commands and high-priority items
      const recent = commands.filter(cmd => recentCommands?.includes(cmd.id));
      const highPriority = commands
        .filter(cmd => (cmd.priority || 0) >= 7 && !recentCommands?.includes(cmd.id))
        .sort((a, b) => (b.priority || 0) - (a.priority || 0));
      
      return [...recent, ...highPriority.slice(0, 8)];
    }

    const queryLower = query.toLowerCase();
    return commands
      .filter(cmd => 
        cmd.title.toLowerCase().includes(queryLower) ||
        cmd.subtitle?.toLowerCase().includes(queryLower) ||
        cmd.category.toLowerCase().includes(queryLower) ||
        cmd.keywords.some(keyword => keyword.toLowerCase().includes(queryLower))
      )
      .sort((a, b) => {
        // Prioritize title matches
        const aTitle = a.title.toLowerCase().includes(queryLower) ? 100 : 0;
        const bTitle = b.title.toLowerCase().includes(queryLower) ? 100 : 0;
        
        return (bTitle + (b.priority || 0)) - (aTitle + (a.priority || 0));
      });
  }, [query, commands, recentCommands]);

  // Group commands by category
  const commandsByCategory = useMemo(() => {
    const groups: Record<string, CommandItem[]> = {};
    filteredCommands.forEach(cmd => {
      if (!groups[cmd.category]) {
        groups[cmd.category] = [];
      }
      groups[cmd.category].push(cmd);
    });
    return groups;
  }, [filteredCommands]);

  // Handle command execution
  const executeCommand = useCallback((command: CommandItem) => {
    // Add to recent commands
    const newRecent = [command.id, ...(recentCommands || []).filter(id => id !== command.id)].slice(0, 10);
    setRecentCommands(newRecent);

    // Execute the command
    command.action();
    
    // Close the palette
    onClose();
    setQuery('');
    setSelectedIndex(0);
  }, [recentCommands, setRecentCommands, onClose]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!open) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, filteredCommands.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          onClose();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, filteredCommands, selectedIndex, executeCommand, onClose]);

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Global shortcut to open command palette
  useHotkeys('ctrl+k, cmd+k', (e) => {
    e.preventDefault();
    if (!open) {
      // Open handled by parent component
    }
  });

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, index) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <Box key={index} component="span" sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', px: 0.5, borderRadius: 0.5 }}>
          {part}
        </Box>
      ) : part
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          bgcolor: alpha(theme.palette.background.paper, 0.95),
          backdropFilter: 'blur(20px)',
        },
      }}
    >
      <AnimatePresence>
        {open && (
          <motion.div
            variants={fadeVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            <DialogContent sx={{ p: 0 }}>
              {/* Search Input */}
              <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
                <TextField
                  fullWidth
                  placeholder="Search commands, pages, or features..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  variant="outlined"
                  autoFocus
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon color="action" />
                      </InputAdornment>
                    ),
                    sx: {
                      '& .MuiOutlinedInput-notchedOutline': {
                        border: 'none',
                      },
                      bgcolor: alpha(theme.palette.background.default, 0.5),
                      borderRadius: 2,
                    },
                  }}
                />
              </Box>

              {/* Results */}
              <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                {filteredCommands.length === 0 ? (
                  <Box sx={{ p: 3, textAlign: 'center' }}>
                    <Typography color="text.secondary">
                      No commands found
                    </Typography>
                  </Box>
                ) : (
                  <motion.div
                    variants={staggerContainer}
                    initial="initial"
                    animate="animate"
                  >
                    {Object.entries(commandsByCategory).map(([category, items], categoryIndex) => (
                      <Box key={category}>
                        {categoryIndex > 0 && <Divider />}
                        
                        {/* Category Header */}
                        <Box sx={{ px: 2, py: 1, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                          <Typography variant="caption" color="primary.main" fontWeight="medium">
                            {category}
                          </Typography>
                          {category === 'Navigation' && !query && (
                            <Chip
                              icon={<History />}
                              label="Recent"
                              size="small"
                              sx={{ ml: 1, height: 20 }}
                            />
                          )}
                        </Box>

                        {/* Commands */}
                        <List sx={{ py: 0 }}>
                          {items.map((command, index) => {
                            const globalIndex = filteredCommands.indexOf(command);
                            const isSelected = globalIndex === selectedIndex;
                            
                            return (
                              <motion.div key={command.id} variants={staggerItem}>
                                <ListItem
                                  button
                                  selected={isSelected}
                                  onClick={() => executeCommand(command)}
                                  sx={{
                                    py: 1.5,
                                    px: 2,
                                    borderRadius: isSelected ? 1 : 0,
                                    mx: isSelected ? 1 : 0,
                                    bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.1) : 'transparent',
                                    '&:hover': {
                                      bgcolor: alpha(theme.palette.primary.main, 0.05),
                                    },
                                  }}
                                >
                                  <ListItemIcon sx={{ color: isSelected ? 'primary.main' : 'action.active' }}>
                                    {command.icon}
                                  </ListItemIcon>
                                  
                                  <ListItemText
                                    primary={
                                      <Typography variant="body2" fontWeight="medium">
                                        {highlightMatch(command.title, query)}
                                      </Typography>
                                    }
                                    secondary={command.subtitle && (
                                      <Typography variant="caption" color="text.secondary">
                                        {highlightMatch(command.subtitle, query)}
                                      </Typography>
                                    )}
                                  />

                                  {recentCommands?.includes(command.id) && (
                                    <Chip
                                      icon={<Star />}
                                      label="Recent"
                                      size="small"
                                      color="primary"
                                      variant="outlined"
                                      sx={{ height: 24 }}
                                    />
                                  )}

                                  <NavigateNext color="action" fontSize="small" />
                                </ListItem>
                              </motion.div>
                            );
                          })}
                        </List>
                      </Box>
                    ))}
                  </motion.div>
                )}
              </Box>

              {/* Footer */}
              <Box sx={{ p: 1.5, borderTop: 1, borderColor: 'divider', bgcolor: alpha(theme.palette.background.default, 0.5) }}>
                <Typography variant="caption" color="text.secondary">
                  Use ↑↓ to navigate, Enter to select, Esc to close
                </Typography>
              </Box>
            </DialogContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Dialog>
  );
};

export default CommandPalette;