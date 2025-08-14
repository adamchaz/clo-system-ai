// Grid compatibility wrapper for Material-UI v7
// Handles the breaking changes in Grid component API

import { Grid as MuiGrid, GridProps } from '@mui/material';
import React from 'react';

interface CompatGridProps extends Omit<GridProps, 'item'> {
  item?: boolean;
  xs?: number | boolean;
  sm?: number | boolean;  
  md?: number | boolean;
  lg?: number | boolean;
  xl?: number | boolean;
}

export const Grid: React.FC<CompatGridProps> = ({ item, children, ...props }) => {
  if (item) {
    return <MuiGrid {...({ item: true } as any)} {...props}>{children}</MuiGrid>;
  }
  return <MuiGrid {...props}>{children}</MuiGrid>;
};

export default Grid;