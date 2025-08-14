import React, { useState, useMemo } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  TablePagination,
  Paper,
  Checkbox,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  TextField,
  InputAdornment,
  Box,
  Typography,
  Chip,
  Tooltip,
  alpha,
  useTheme,
} from '@mui/material';
import {
  Search,
  TrendingUp,
  TrendingDown,
  MoreVert,
} from '@mui/icons-material';

export interface DataTableColumn<T = any> {
  id: keyof T | string;
  label: string;
  minWidth?: number;
  maxWidth?: number;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  filterable?: boolean;
  format?: (value: any, row: T) => React.ReactNode;
  render?: (value: any, row: T) => React.ReactNode;
  headerRender?: () => React.ReactNode;
}

export interface DataTableAction<T = any> {
  icon: React.ComponentType;
  label: string;
  onClick: (row: T) => void;
  color?: 'primary' | 'secondary' | 'error' | 'warning' | 'info' | 'success';
  disabled?: (row: T) => boolean;
  hidden?: (row: T) => boolean;
}

export interface DataTableProps<T = any> {
  columns: DataTableColumn<T>[];
  data: T[];
  loading?: boolean;
  selectable?: boolean;
  searchable?: boolean;
  filterable?: boolean;
  exportable?: boolean;
  actions?: DataTableAction<T>[];
  rowActions?: DataTableAction<T>[];
  onRowClick?: (row: T) => void;
  onSelectionChange?: (selectedRows: T[]) => void;
  onExport?: (data: T[]) => void;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  searchPlaceholder?: string;
  emptyMessage?: string;
  pageSize?: number;
  pageSizeOptions?: number[];
  maxHeight?: number | string;
  stickyHeader?: boolean;
  striped?: boolean;
  hover?: boolean;
  dense?: boolean;
  title?: string;
  subtitle?: string;
}

type SortOrder = 'asc' | 'desc';

interface SortState {
  column: string;
  direction: SortOrder;
}

const DataTable = <T extends Record<string, any>>({
  columns,
  data,
  loading = false,
  selectable = false,
  searchable = true,
  // filterable = false,
  // exportable = false,
  actions = [],
  rowActions = [],
  onRowClick,
  onSelectionChange,
  // onExport,
  sortBy,
  sortOrder = 'asc',
  searchPlaceholder = 'Search...',
  emptyMessage = 'No data available',
  pageSize = 25,
  pageSizeOptions = [10, 25, 50, 100],
  maxHeight = 'none',
  stickyHeader = true,
  striped = true,
  hover = true,
  dense = false,
  title,
  subtitle,
}: DataTableProps<T>) => {
  const theme = useTheme();
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(pageSize);
  const [selected, setSelected] = useState<T[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sort, setSort] = useState<SortState>({
    column: sortBy || '',
    direction: sortOrder,
  });
  const [actionAnchor, setActionAnchor] = useState<{
    element: HTMLElement;
    row: T;
  } | null>(null);

  // Memoized filtered and sorted data
  const processedData = useMemo(() => {
    let result = [...data];

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      result = result.filter((row) =>
        columns.some((column) => {
          const value = row[column.id as keyof T];
          return String(value).toLowerCase().includes(searchLower);
        })
      );
    }

    // Apply sorting
    if (sort.column) {
      result.sort((a, b) => {
        const aValue = a[sort.column as keyof T];
        const bValue = b[sort.column as keyof T];
        
        let comparison = 0;
        if (aValue < bValue) comparison = -1;
        if (aValue > bValue) comparison = 1;
        
        return sort.direction === 'desc' ? -comparison : comparison;
      });
    }

    return result;
  }, [data, searchTerm, sort, columns]);

  // Pagination
  const paginatedData = useMemo(() => {
    const start = page * rowsPerPage;
    return processedData.slice(start, start + rowsPerPage);
  }, [processedData, page, rowsPerPage]);

  const handleSort = (columnId: string) => {
    const column = columns.find(col => col.id === columnId);
    if (!column?.sortable) return;

    const isCurrentColumn = sort.column === columnId;
    setSort({
      column: columnId,
      direction: isCurrentColumn && sort.direction === 'asc' ? 'desc' : 'asc',
    });
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelected([...paginatedData]);
      onSelectionChange?.(paginatedData);
    } else {
      setSelected([]);
      onSelectionChange?.([]);
    }
  };

  const handleSelectRow = (row: T) => {
    const selectedIndex = selected.indexOf(row);
    let newSelected: T[] = [];

    if (selectedIndex === -1) {
      newSelected = [...selected, row];
    } else {
      newSelected = selected.filter(item => item !== row);
    }

    setSelected(newSelected);
    onSelectionChange?.(newSelected);
  };

  const isSelected = (row: T) => selected.indexOf(row) !== -1;

  const handleRowActionsClick = (event: React.MouseEvent<HTMLElement>, row: T) => {
    event.stopPropagation();
    setActionAnchor({ element: event.currentTarget, row });
  };

  const handleRowActionsClose = () => {
    setActionAnchor(null);
  };

  const getCellValue = (row: T, column: DataTableColumn<T>) => {
    const value = row[column.id as keyof T];
    
    if (column.render) {
      return column.render(value, row);
    }
    
    if (column.format) {
      return column.format(value, row);
    }
    
    return value;
  };

  const formatValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span style={{ color: theme.palette.text.disabled }}>—</span>;
    }
    
    if (typeof value === 'number') {
      // Check if it's a percentage
      if (Math.abs(value) < 1 && value !== 0) {
        return (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {value > 0 ? (
              <TrendingUp color="success" sx={{ mr: 0.5, fontSize: 16 }} />
            ) : (
              <TrendingDown color="error" sx={{ mr: 0.5, fontSize: 16 }} />
            )}
            {(value * 100).toFixed(2)}%
          </Box>
        );
      }
      return value.toLocaleString();
    }
    
    if (typeof value === 'boolean') {
      return (
        <Chip
          label={value ? 'Yes' : 'No'}
          color={value ? 'success' : 'default'}
          size="small"
        />
      );
    }
    
    return String(value);
  };

  return (
    <Paper elevation={1} sx={{ width: '100%' }}>
      {/* Header */}
      {(title || subtitle || searchable || actions.length > 0) && (
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: searchable ? 2 : 0 }}>
            <Box>
              {title && (
                <Typography variant="h6" component="h2">
                  {title}
                </Typography>
              )}
              {subtitle && (
                <Typography variant="body2" color="text.secondary">
                  {subtitle}
                </Typography>
              )}
            </Box>
            
            {actions.length > 0 && (
              <Box sx={{ display: 'flex', gap: 1 }}>
                {actions.map((action, index) => (
                  <Tooltip key={index} title={action.label}>
                    <IconButton
                      onClick={() => action.onClick(processedData as any)}
                      color={action.color || 'default'}
                      disabled={action.disabled?.(processedData as any)}
                    >
                      {React.createElement(action.icon)}
                    </IconButton>
                  </Tooltip>
                ))}
              </Box>
            )}
          </Box>
          
          {searchable && (
            <TextField
              size="small"
              placeholder={searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search />
                  </InputAdornment>
                ),
              }}
              sx={{ width: { xs: '100%', sm: 300 } }}
            />
          )}
        </Box>
      )}

      {/* Table */}
      <TableContainer sx={{ maxHeight, overflow: 'auto' }}>
        <Table stickyHeader={stickyHeader} size={dense ? 'small' : 'medium'}>
          <TableHead>
            <TableRow>
              {selectable && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={selected.length > 0 && selected.length < paginatedData.length}
                    checked={paginatedData.length > 0 && selected.length === paginatedData.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
              )}
              
              {columns.map((column) => (
                <TableCell
                  key={String(column.id)}
                  align={column.align || 'left'}
                  style={{
                    minWidth: column.minWidth,
                    maxWidth: column.maxWidth,
                    width: column.width,
                  }}
                  sortDirection={sort.column === column.id ? sort.direction : false}
                >
                  {column.sortable ? (
                    <TableSortLabel
                      active={sort.column === column.id}
                      direction={sort.column === column.id ? sort.direction : 'asc'}
                      onClick={() => handleSort(String(column.id))}
                    >
                      {column.headerRender ? column.headerRender() : column.label}
                    </TableSortLabel>
                  ) : (
                    column.headerRender ? column.headerRender() : column.label
                  )}
                </TableCell>
              ))}
              
              {rowActions.length > 0 && (
                <TableCell align="center" style={{ width: 60 }}>
                  Actions
                </TableCell>
              )}
            </TableRow>
          </TableHead>
          
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={columns.length + (selectable ? 1 : 0) + (rowActions.length > 0 ? 1 : 0)}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <Typography color="text.secondary">Loading...</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : paginatedData.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length + (selectable ? 1 : 0) + (rowActions.length > 0 ? 1 : 0)}>
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <Typography color="text.secondary">{emptyMessage}</Typography>
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              paginatedData.map((row, index) => {
                const isItemSelected = isSelected(row);
                
                return (
                  <TableRow
                    key={index}
                    hover={hover}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    role={onRowClick ? 'button' : undefined}
                    tabIndex={onRowClick ? 0 : -1}
                    selected={isItemSelected}
                    sx={{
                      cursor: onRowClick ? 'pointer' : 'default',
                      ...(striped && index % 2 === 1 && {
                        backgroundColor: alpha(theme.palette.primary.main, 0.02),
                      }),
                    }}
                  >
                    {selectable && (
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={isItemSelected}
                          onChange={() => handleSelectRow(row)}
                          onClick={(e) => e.stopPropagation()}
                        />
                      </TableCell>
                    )}
                    
                    {columns.map((column) => (
                      <TableCell
                        key={String(column.id)}
                        align={column.align || 'left'}
                        style={{
                          minWidth: column.minWidth,
                          maxWidth: column.maxWidth,
                          width: column.width,
                        }}
                      >
                        {formatValue(getCellValue(row, column))}
                      </TableCell>
                    ))}
                    
                    {rowActions.length > 0 && (
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={(e) => handleRowActionsClick(e, row)}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    )}
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination */}
      {!loading && processedData.length > 0 && (
        <TablePagination
          rowsPerPageOptions={pageSizeOptions}
          component="div"
          count={processedData.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      )}

      {/* Row Actions Menu */}
      {rowActions.length > 0 && (
        <Menu
          anchorEl={actionAnchor?.element}
          open={Boolean(actionAnchor)}
          onClose={handleRowActionsClose}
          onClick={handleRowActionsClose}
        >
          {rowActions.map((action, index) => {
            const row = actionAnchor?.row;
            if (!row || action.hidden?.(row)) return null;
            
            return (
              <MenuItem
                key={index}
                onClick={() => {
                  action.onClick(row);
                  handleRowActionsClose();
                }}
                disabled={action.disabled?.(row)}
              >
                <ListItemIcon>
                  {React.createElement(action.icon)}
                </ListItemIcon>
                <ListItemText>{action.label}</ListItemText>
              </MenuItem>
            );
          })}
        </Menu>
      )}
    </Paper>
  );
};

export default DataTable;