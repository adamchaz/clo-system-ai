/**
 * Concentration Test Mappings and Definitions
 * Maps test numbers to their names and categories based on VBA TestNum enum
 */

export interface ConcentrationTestDefinition {
  testNumber: number;
  testName: string;
  category: 'asset_quality' | 'geographic' | 'industry' | 'collateral_quality';
  description: string;
  thresholdType: 'minimum' | 'maximum';
  displayFormat: 'percentage' | 'number' | 'ratio';
}

export const CONCENTRATION_TEST_DEFINITIONS: Record<number, ConcentrationTestDefinition> = {
  // Asset Quality Tests (1-13, 28-31, 40, 44)
  1: {
    testNumber: 1,
    testName: 'Limitation on Senior Secured Loans',
    category: 'asset_quality',
    description: 'Minimum percentage of senior secured loans required',
    thresholdType: 'minimum',
    displayFormat: 'percentage'
  },
  2: {
    testNumber: 2,
    testName: 'Limitation on non Senior Secured Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of non-senior secured loans allowed',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  3: {
    testNumber: 3,
    testName: 'Limitation on 6th Largest Obligor',
    category: 'asset_quality',
    description: 'Maximum exposure to 6th largest obligor',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  4: {
    testNumber: 4,
    testName: 'Limitation on 1st Largest Obligor',
    category: 'asset_quality',
    description: 'Maximum exposure to largest obligor',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  5: {
    testNumber: 5,
    testName: 'Limitation on DIP Obligor',
    category: 'asset_quality',
    description: 'Maximum exposure to DIP obligor',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  6: {
    testNumber: 6,
    testName: 'Limitation on Non Senior Secured Obligor',
    category: 'asset_quality',
    description: 'Maximum exposure to non-senior secured obligor',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  7: {
    testNumber: 7,
    testName: 'Limitation on Caa Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of Caa rated loans',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  8: {
    testNumber: 8,
    testName: 'Limitation on Assets Pay Less Frequently than Quarterly',
    category: 'asset_quality',
    description: 'Maximum percentage of assets paying less than quarterly',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  9: {
    testNumber: 9,
    testName: 'Limitation on Fixed Rate Assets',
    category: 'asset_quality',
    description: 'Maximum percentage of fixed rate assets',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  10: {
    testNumber: 10,
    testName: 'Limitation on Current Pay Obligations',
    category: 'asset_quality',
    description: 'Maximum percentage of current pay obligations',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  11: {
    testNumber: 11,
    testName: 'Limitation on DIP Obligations',
    category: 'asset_quality',
    description: 'Maximum percentage of DIP obligations',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  12: {
    testNumber: 12,
    testName: 'Limitation on Unfunded Commitments',
    category: 'asset_quality',
    description: 'Maximum percentage of unfunded commitments',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  13: {
    testNumber: 13,
    testName: 'Limitation on Participation Interest',
    category: 'asset_quality',
    description: 'Maximum percentage of participation interests',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  
  // Geographic Tests (14-24, 41, 47)
  14: {
    testNumber: 14,
    testName: 'Limitation on Countries Not US',
    category: 'geographic',
    description: 'Maximum exposure to non-US countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  15: {
    testNumber: 15,
    testName: 'Limitation on Countries Canada and Tax Jurisdictions',
    category: 'geographic',
    description: 'Maximum exposure to Canada and tax jurisdictions',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  16: {
    testNumber: 16,
    testName: 'Limitation on Countries Not US Canada UK',
    category: 'geographic',
    description: 'Maximum exposure to countries other than US, Canada, UK',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  17: {
    testNumber: 17,
    testName: 'Limitation on Group Countries',
    category: 'geographic',
    description: 'Maximum exposure to group countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  18: {
    testNumber: 18,
    testName: 'Limitation on Group I Countries',
    category: 'geographic',
    description: 'Maximum exposure to Group I countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  19: {
    testNumber: 19,
    testName: 'Limitation on Individual Group I Countries',
    category: 'geographic',
    description: 'Maximum exposure to individual Group I countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  20: {
    testNumber: 20,
    testName: 'Limitation on Group II Countries',
    category: 'geographic',
    description: 'Maximum exposure to Group II countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  21: {
    testNumber: 21,
    testName: 'Limitation on Individual Group II Countries',
    category: 'geographic',
    description: 'Maximum exposure to individual Group II countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  22: {
    testNumber: 22,
    testName: 'Limitation on Group III Countries',
    category: 'geographic',
    description: 'Maximum exposure to Group III countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  23: {
    testNumber: 23,
    testName: 'Limitation on Individual Group III Countries',
    category: 'geographic',
    description: 'Maximum exposure to individual Group III countries',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  24: {
    testNumber: 24,
    testName: 'Limitation on Tax Jurisdictions',
    category: 'geographic',
    description: 'Maximum exposure to tax haven jurisdictions',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  
  // Industry Tests (25-27, 48-53)
  25: {
    testNumber: 25,
    testName: 'Limitation on 4th Largest SP Industry Classification',
    category: 'industry',
    description: 'Maximum exposure to 4th largest S&P industry',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  26: {
    testNumber: 26,
    testName: 'Limitation on 2nd Largest SP Classification',
    category: 'industry',
    description: 'Maximum exposure to 2nd largest S&P classification',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  27: {
    testNumber: 27,
    testName: 'Limitation on 1st Largest SP Classification',
    category: 'industry',
    description: 'Maximum exposure to largest S&P classification',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  
  // More Asset Quality Tests
  28: {
    testNumber: 28,
    testName: 'Limitation on Bridge Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of bridge loans',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  29: {
    testNumber: 29,
    testName: 'Limitation on Cov Lite Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of covenant lite loans',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  30: {
    testNumber: 30,
    testName: 'Limitation on Deferrable Securities',
    category: 'asset_quality',
    description: 'Maximum percentage of deferrable securities',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  31: {
    testNumber: 31,
    testName: 'Limitation on Facility Size',
    category: 'asset_quality',
    description: 'Maximum facility size concentration',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  
  // Collateral Quality Tests (32-39, 46, 54)
  32: {
    testNumber: 32,
    testName: 'Weighted Average Spread',
    category: 'collateral_quality',
    description: 'Minimum weighted average spread',
    thresholdType: 'minimum',
    displayFormat: 'number'
  },
  33: {
    testNumber: 33,
    testName: 'Weighted Average Recovery Rate',
    category: 'collateral_quality',
    description: 'Minimum weighted average Moody recovery rate',
    thresholdType: 'minimum',
    displayFormat: 'percentage'
  },
  34: {
    testNumber: 34,
    testName: 'Weighted Average Coupon',
    category: 'collateral_quality',
    description: 'Minimum weighted average coupon',
    thresholdType: 'minimum',
    displayFormat: 'percentage'
  },
  35: {
    testNumber: 35,
    testName: 'Weighted Average Life',
    category: 'collateral_quality',
    description: 'Maximum weighted average life in years',
    thresholdType: 'maximum',
    displayFormat: 'number'
  },
  36: {
    testNumber: 36,
    testName: 'Weighted Average Rating Factor',
    category: 'collateral_quality',
    description: 'Maximum weighted average rating factor (WARF)',
    thresholdType: 'maximum',
    displayFormat: 'number'
  },
  37: {
    testNumber: 37,
    testName: 'Moody Diversity Test',
    category: 'collateral_quality',
    description: 'Minimum Moody diversity score',
    thresholdType: 'minimum',
    displayFormat: 'number'
  },
  38: {
    testNumber: 38,
    testName: 'JROC Test',
    category: 'collateral_quality',
    description: 'Junior Relative Overcollateralization test',
    thresholdType: 'minimum',
    displayFormat: 'number'
  },
  39: {
    testNumber: 39,
    testName: 'Weighted Average Spread MAG14',
    category: 'collateral_quality',
    description: 'Minimum weighted average spread for MAG14',
    thresholdType: 'minimum',
    displayFormat: 'number'
  },
  
  // More Asset Quality Tests
  40: {
    testNumber: 40,
    testName: 'Limitation on CCC Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of CCC rated loans',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  41: {
    testNumber: 41,
    testName: 'Limitation on Canada',
    category: 'geographic',
    description: 'Maximum exposure to Canada',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  42: {
    testNumber: 42,
    testName: 'Limitation on Letter of Credit',
    category: 'asset_quality',
    description: 'Maximum percentage of letter of credit obligations',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  43: {
    testNumber: 43,
    testName: 'Limitation on Long Dated',
    category: 'asset_quality',
    description: 'Maximum percentage of long dated obligations',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  44: {
    testNumber: 44,
    testName: 'Limitation on Unsecured Loans',
    category: 'asset_quality',
    description: 'Maximum percentage of unsecured loans',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  45: {
    testNumber: 45,
    testName: 'Limitation on Swap Non Discount',
    category: 'asset_quality',
    description: 'Maximum percentage of non-discount swap obligations',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  46: {
    testNumber: 46,
    testName: 'Weighted Average Spread MAG06',
    category: 'collateral_quality',
    description: 'Minimum weighted average spread for MAG06',
    thresholdType: 'minimum',
    displayFormat: 'number'
  },
  47: {
    testNumber: 47,
    testName: 'Limitation on Non-Emerging Market Obligors',
    category: 'geographic',
    description: 'Maximum exposure to non-emerging market obligors',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  48: {
    testNumber: 48,
    testName: 'Limitation on SP Criteria',
    category: 'industry',
    description: 'Maximum exposure based on S&P criteria',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  49: {
    testNumber: 49,
    testName: 'Limitation on 1st Moody Industry',
    category: 'industry',
    description: 'Maximum exposure to largest Moody industry',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  50: {
    testNumber: 50,
    testName: 'Limitation on 2nd Moody Industry',
    category: 'industry',
    description: 'Maximum exposure to 2nd largest Moody industry',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  51: {
    testNumber: 51,
    testName: 'Limitation on 3rd Moody Industry',
    category: 'industry',
    description: 'Maximum exposure to 3rd largest Moody industry',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  52: {
    testNumber: 52,
    testName: 'Limitation on 4th Moody Industry',
    category: 'industry',
    description: 'Maximum exposure to 4th largest Moody industry',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  53: {
    testNumber: 53,
    testName: 'Limitation on Facility Size MAG08',
    category: 'industry',
    description: 'Maximum facility size for MAG08',
    thresholdType: 'maximum',
    displayFormat: 'percentage'
  },
  54: {
    testNumber: 54,
    testName: 'Weighted Average Rating Factor MAG14',
    category: 'collateral_quality',
    description: 'Maximum weighted average rating factor for MAG14',
    thresholdType: 'maximum',
    displayFormat: 'number'
  }
};

/**
 * Get test definition by test number
 */
export function getTestDefinition(testNumber: number): ConcentrationTestDefinition | undefined {
  return CONCENTRATION_TEST_DEFINITIONS[testNumber];
}

/**
 * Get test name by test number
 */
export function getTestName(testNumber: number): string {
  const definition = CONCENTRATION_TEST_DEFINITIONS[testNumber];
  return definition?.testName || `Test ${testNumber}`;
}

/**
 * Get test category by test number
 */
export function getTestCategory(testNumber: number): string {
  const definition = CONCENTRATION_TEST_DEFINITIONS[testNumber];
  return definition?.category || 'collateral_quality';
}

/**
 * Format test value based on display format
 */
export function formatTestValue(value: number, testNumber: number): string {
  const definition = CONCENTRATION_TEST_DEFINITIONS[testNumber];
  const format = definition?.displayFormat || 'percentage';
  
  switch (format) {
    case 'percentage':
      return `${(value * 100).toFixed(2)}%`;
    case 'number':
      return value.toFixed(2);
    case 'ratio':
      return `${value.toFixed(2)}x`;
    default:
      return value.toString();
  }
}

/**
 * Get threshold symbol based on threshold type
 */
export function getThresholdSymbol(testNumber: number): string {
  const definition = CONCENTRATION_TEST_DEFINITIONS[testNumber];
  return definition?.thresholdType === 'minimum' ? '≥' : '≤';
}