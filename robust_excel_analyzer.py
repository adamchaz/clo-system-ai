#!/usr/bin/env python3
"""
Robust Excel Analyzer for CLO System
Handles various Excel complexities and provides comprehensive business logic analysis
"""

import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

class RobustCLOAnalyzer:
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.analysis_results = {}
        
    def analyze_complete_system(self) -> Dict[str, Any]:
        """Complete analysis of the CLO Excel system"""
        print("=" * 80)
        print("ROBUST CLO EXCEL SYSTEM ANALYSIS")
        print("=" * 80)
        
        # 1. Basic file structure from ZIP
        self._analyze_excel_structure()
        
        # 2. Worksheet analysis using XML parsing (more robust)
        self._analyze_worksheets_xml()
        
        # 3. VBA analysis
        self._analyze_vba_components()
        
        # 4. Business logic inference
        self._infer_clo_business_logic()
        
        # 5. Data relationships
        self._analyze_data_relationships()
        
        # 6. Generate comprehensive report
        self._generate_final_report()
        
        return self.analysis_results
    
    def _analyze_excel_structure(self):
        """Analyze Excel file structure from ZIP"""
        print("\n1. EXCEL FILE STRUCTURE ANALYSIS")
        print("-" * 50)
        
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
                files = zip_ref.namelist()
                
                structure = {
                    'total_files': len(files),
                    'worksheets': [f for f in files if f.startswith('xl/worksheets/')],
                    'vba_files': [f for f in files if 'vbaProject' in f or 'vba' in f.lower()],
                    'external_links': [f for f in files if 'external' in f.lower()],
                    'connections': [f for f in files if 'connection' in f.lower()],
                    'pivot_tables': [f for f in files if 'pivotTable' in f],
                    'charts': [f for f in files if 'chart' in f],
                    'drawings': [f for f in files if 'drawing' in f],
                    'custom_xml': [f for f in files if 'customXml' in f]
                }
                
                self.analysis_results['file_structure'] = structure
                
                print(f"Total files in Excel package: {structure['total_files']}")
                print(f"Worksheet files: {len(structure['worksheets'])}")
                print(f"VBA project files: {len(structure['vba_files'])}")
                print(f"External connections: {len(structure['connections'])}")
                print(f"Pivot tables: {len(structure['pivot_tables'])}")
                print(f"Charts/Graphics: {len(structure['charts']) + len(structure['drawings'])}")
                
        except Exception as e:
            print(f"Error analyzing file structure: {e}")
    
    def _analyze_worksheets_xml(self):
        """Analyze worksheets using XML parsing for robustness"""
        print("\n2. WORKSHEET ANALYSIS (XML-based)")
        print("-" * 50)
        
        worksheets = {}
        
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
                # First, get worksheet names from workbook.xml
                worksheet_names = self._get_worksheet_names(zip_ref)
                
                # Analyze each worksheet
                for i, ws_file in enumerate(self.analysis_results['file_structure']['worksheets']):
                    try:
                        sheet_name = worksheet_names.get(i, f"Sheet{i+1}")
                        print(f"\nAnalyzing: {sheet_name}")
                        
                        ws_analysis = self._analyze_single_worksheet_xml(zip_ref, ws_file, sheet_name)
                        worksheets[sheet_name] = ws_analysis
                        
                        # Print summary
                        print(f"  Dimensions: {ws_analysis['dimensions']['rows']}x{ws_analysis['dimensions']['cols']}")
                        print(f"  Formulas: {ws_analysis['formulas']['count']}")
                        print(f"  Data cells: {ws_analysis['data']['cell_count']}")
                        
                    except Exception as e:
                        print(f"  Error analyzing {ws_file}: {e}")
                        continue
                
                self.analysis_results['worksheets'] = worksheets
                
        except Exception as e:
            print(f"Error in worksheet analysis: {e}")
    
    def _get_worksheet_names(self, zip_ref) -> Dict[int, str]:
        """Extract worksheet names from workbook.xml"""
        worksheet_names = {}
        
        try:
            with zip_ref.open('xl/workbook.xml') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                # Find all sheet elements
                for sheet in root.iter():
                    if sheet.tag.endswith('sheet'):
                        name = sheet.get('name')
                        sheet_id = int(sheet.get('sheetId', 0)) - 1  # Convert to 0-based index
                        if name:
                            worksheet_names[sheet_id] = name
                            
        except Exception as e:
            print(f"Error getting worksheet names: {e}")
            
        return worksheet_names
    
    def _analyze_single_worksheet_xml(self, zip_ref, ws_file: str, sheet_name: str) -> Dict[str, Any]:
        """Analyze a single worksheet using XML"""
        analysis = {
            'name': sheet_name,
            'file': ws_file,
            'dimensions': {'rows': 0, 'cols': 0},
            'formulas': {'count': 0, 'samples': [], 'functions_used': {}},
            'data': {'cell_count': 0, 'sample_values': []},
            'business_indicators': {
                'clo_keywords': {},
                'data_patterns': [],
                'sheet_purpose': 'Unknown'
            }
        }
        
        try:
            with zip_ref.open(ws_file) as f:
                tree = ET.parse(f)
                root = tree.getroot()
                
                # Count rows and columns
                max_row = 0
                max_col = 0
                cell_count = 0
                formula_count = 0
                
                # Parse all cells
                for cell in root.iter():
                    if cell.tag.endswith('c'):  # Cell element
                        cell_count += 1
                        
                        # Get cell reference
                        cell_ref = cell.get('r', '')
                        if cell_ref:
                            col_str = ''.join(filter(str.isalpha, cell_ref))
                            row_str = ''.join(filter(str.isdigit, cell_ref))
                            
                            if row_str:
                                max_row = max(max_row, int(row_str))
                            
                            if col_str:
                                col_num = self._column_string_to_number(col_str)
                                max_col = max(max_col, col_num)
                        
                        # Check for formulas
                        for child in cell:
                            if child.tag.endswith('f'):  # Formula element
                                formula_count += 1
                                formula_text = child.text
                                
                                if formula_text and len(analysis['formulas']['samples']) < 20:
                                    analysis['formulas']['samples'].append({
                                        'cell': cell_ref,
                                        'formula': formula_text[:100]
                                    })
                                
                                # Count function usage
                                if formula_text:
                                    functions = re.findall(r'([A-Z]{2,})\s*\(', formula_text)
                                    for func in functions:
                                        analysis['formulas']['functions_used'][func] = \
                                            analysis['formulas']['functions_used'].get(func, 0) + 1
                            
                            elif child.tag.endswith('v'):  # Value element
                                value = child.text
                                if value and len(analysis['data']['sample_values']) < 50:
                                    analysis['data']['sample_values'].append({
                                        'cell': cell_ref,
                                        'value': str(value)[:100]
                                    })
                
                analysis['dimensions'] = {'rows': max_row, 'cols': max_col}
                analysis['formulas']['count'] = formula_count
                analysis['data']['cell_count'] = cell_count
                
                # Analyze for CLO business logic
                self._identify_sheet_business_logic(analysis)
                
        except Exception as e:
            print(f"    Warning: Could not fully parse {ws_file}: {e}")
            # Set basic info even if parsing fails
            analysis['business_indicators']['sheet_purpose'] = self._infer_purpose_from_name(sheet_name)
        
        return analysis
    
    def _column_string_to_number(self, col_str: str) -> int:
        """Convert Excel column string to number (A=1, B=2, etc.)"""
        result = 0
        for char in col_str.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result
    
    def _identify_sheet_business_logic(self, sheet_analysis):
        """Identify CLO business logic in sheet data"""
        sheet_name = sheet_analysis['name'].lower()
        
        # Keywords categorized by CLO function
        clo_categories = {
            'portfolio_management': ['portfolio', 'asset', 'loan', 'security', 'position', 'holding'],
            'risk_analysis': ['default', 'recovery', 'loss', 'rating', 'spread', 'correlation', 'probability'],
            'compliance_testing': ['coverage', 'ratio', 'test', 'compliance', 'overcollateralization', 'oc'],
            'cash_flow_modeling': ['cashflow', 'payment', 'interest', 'principal', 'coupon', 'yield', 'discount'],
            'scenario_analysis': ['simulation', 'monte carlo', 'scenario', 'stress', 'hypothesis', 'magnitude'],
            'valuation': ['npv', 'pv', 'fair value', 'mark', 'price', 'valuation', 'market value'],
            'trading': ['buy', 'sell', 'trade', 'execute', 'order', 'transaction'],
            'reporting': ['report', 'summary', 'output', 'dashboard', 'ranking']
        }
        
        # Count keyword occurrences
        keyword_counts = {category: 0 for category in clo_categories}
        
        # Check sheet name
        for category, keywords in clo_categories.items():
            for keyword in keywords:
                if keyword in sheet_name:
                    keyword_counts[category] += 5  # Weight sheet name matches higher
        
        # Check sample values
        all_text = ' '.join([sample['value'].lower() for sample in sheet_analysis['data']['sample_values'] 
                           if isinstance(sample['value'], str)])
        
        # Check formulas
        all_formulas = ' '.join([sample['formula'].lower() for sample in sheet_analysis['formulas']['samples']])
        
        combined_text = f"{sheet_name} {all_text} {all_formulas}"
        
        for category, keywords in clo_categories.items():
            for keyword in keywords:
                keyword_counts[category] += combined_text.count(keyword)
        
        # Store significant categories
        significant_categories = {cat: count for cat, count in keyword_counts.items() if count > 0}
        sheet_analysis['business_indicators']['clo_keywords'] = significant_categories
        
        # Determine primary sheet purpose
        if significant_categories:
            primary_purpose = max(significant_categories, key=significant_categories.get)
            sheet_analysis['business_indicators']['sheet_purpose'] = self._map_category_to_purpose(primary_purpose)
        else:
            sheet_analysis['business_indicators']['sheet_purpose'] = self._infer_purpose_from_name(sheet_analysis['name'])
    
    def _map_category_to_purpose(self, category: str) -> str:
        """Map CLO category to business purpose"""
        purpose_mapping = {
            'portfolio_management': 'Portfolio Management & Asset Data',
            'risk_analysis': 'Risk Analysis & Credit Assessment',
            'compliance_testing': 'Regulatory Compliance Testing',
            'cash_flow_modeling': 'Cash Flow Modeling & Analysis',
            'scenario_analysis': 'Scenario Testing & Sensitivity Analysis',
            'valuation': 'Asset Valuation & Pricing',
            'trading': 'Trading Operations & Execution',
            'reporting': 'Reporting & Output Generation'
        }
        return purpose_mapping.get(category, 'General CLO Operations')
    
    def _infer_purpose_from_name(self, sheet_name: str) -> str:
        """Infer sheet purpose from name"""
        name_lower = sheet_name.lower()
        
        if 'input' in name_lower:
            return 'Data Input Sheet'
        elif 'output' in name_lower:
            return 'Results & Reporting Sheet'
        elif 'model' in name_lower or 'run' in name_lower:
            return 'Model Control & Execution'
        elif 'asset' in name_lower:
            return 'Asset Data Management'
        elif 'correlation' in name_lower:
            return 'Asset Correlation Analysis'
        elif 'reference' in name_lower:
            return 'Reference Data & Lookups'
        elif 'mag' in name_lower:
            return 'Magnitude/Sensitivity Analysis'
        elif 'hypo' in name_lower:
            return 'Hypothesis Testing'
        elif 'ranking' in name_lower:
            return 'Asset Ranking & Selection'
        elif 'rebalance' in name_lower:
            return 'Portfolio Rebalancing'
        elif 'filter' in name_lower:
            return 'Data Filtering & Screening'
        else:
            return 'General Worksheet'
    
    def _analyze_vba_components(self):
        """Analyze VBA components"""
        print("\n3. VBA COMPONENT ANALYSIS")
        print("-" * 50)
        
        vba_analysis = {
            'has_vba': False,
            'vba_files': [],
            'estimated_complexity': 'Low',
            'business_functions': []
        }
        
        try:
            with zipfile.ZipFile(self.filepath, 'r') as zip_ref:
                vba_files = [f for f in zip_ref.namelist() if 'vbaProject' in f or 'vba' in f.lower()]
                
                if vba_files:
                    vba_analysis['has_vba'] = True
                    vba_analysis['vba_files'] = vba_files
                    
                    print(f"VBA files found: {len(vba_files)}")
                    for vba_file in vba_files:
                        print(f"  - {vba_file}")
                        
                        try:
                            # Basic VBA content analysis
                            vba_content = zip_ref.read(vba_file)
                            
                            # Check for various VBA patterns
                            if b'Sub ' in vba_content or b'Function ' in vba_content:
                                vba_analysis['business_functions'].append('Custom subroutines and functions')
                                vba_analysis['estimated_complexity'] = 'Medium'
                            
                            if b'Solver' in vba_content:
                                vba_analysis['business_functions'].append('Excel Solver integration')
                                vba_analysis['estimated_complexity'] = 'High'
                            
                            if b'ADODB' in vba_content or b'SQL' in vba_content:
                                vba_analysis['business_functions'].append('Database connectivity')
                                vba_analysis['estimated_complexity'] = 'High'
                            
                            if b'Application.' in vba_content:
                                vba_analysis['business_functions'].append('Excel application automation')
                            
                            # CLO-specific VBA functionality
                            clo_vba_keywords = [b'portfolio', b'correlation', b'simulation', b'monte', 
                                              b'default', b'recovery', b'rating', b'compliance']
                            
                            for keyword in clo_vba_keywords:
                                if keyword in vba_content.lower():
                                    vba_analysis['business_functions'].append(f'CLO logic: {keyword.decode()}')
                        
                        except Exception as e:
                            print(f"    Error analyzing {vba_file}: {e}")
                else:
                    print("No VBA files found")
                
                self.analysis_results['vba_analysis'] = vba_analysis
                
        except Exception as e:
            print(f"Error in VBA analysis: {e}")
    
    def _infer_clo_business_logic(self):
        """Infer overall CLO business logic from analysis"""
        print("\n4. CLO BUSINESS LOGIC INFERENCE")
        print("-" * 50)
        
        business_logic = {
            'system_type': 'CLO Portfolio Management & Analysis System',
            'core_functions': [],
            'data_flow': {},
            'business_processes': [],
            'complexity_assessment': {}
        }
        
        # Analyze worksheet purposes
        sheet_purposes = {}
        for sheet_name, sheet_data in self.analysis_results.get('worksheets', {}).items():
            purpose = sheet_data['business_indicators']['sheet_purpose']
            if purpose not in sheet_purposes:
                sheet_purposes[purpose] = []
            sheet_purposes[purpose].append(sheet_name)
        
        # Identify core functions
        core_functions = []
        
        if any('Portfolio' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Portfolio Management & Asset Tracking')
        
        if any('Risk' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Risk Analysis & Credit Assessment')
        
        if any('Compliance' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Regulatory Compliance Monitoring')
        
        if any('Cash Flow' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Cash Flow Modeling & Projection')
        
        if any('Scenario' in purpose or 'Sensitivity' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Scenario Analysis & Stress Testing')
        
        if any('Valuation' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Asset Valuation & Pricing')
        
        if any('Trading' in purpose for purpose in sheet_purposes.keys()):
            core_functions.append('Trading Operations & Execution')
        
        business_logic['core_functions'] = core_functions
        
        # Business processes
        processes = []
        
        # Look for magnitude analysis sheets
        mag_sheets = [name for name in self.analysis_results.get('worksheets', {}).keys() 
                     if 'mag' in name.lower()]
        if mag_sheets:
            processes.append(f'Magnitude Analysis Workflow ({len(mag_sheets)} scenarios)')
        
        # Look for hypothesis testing
        hypo_sheets = [name for name in self.analysis_results.get('worksheets', {}).keys() 
                      if 'hypo' in name.lower()]
        if hypo_sheets:
            processes.append(f'Hypothesis Testing Framework ({len(hypo_sheets)} tests)')
        
        # Look for input/output workflow
        input_sheets = [name for name in self.analysis_results.get('worksheets', {}).keys() 
                       if 'input' in name.lower()]
        output_sheets = [name for name in self.analysis_results.get('worksheets', {}).keys() 
                        if 'output' in name.lower()]
        
        if input_sheets and output_sheets:
            processes.append(f'Data Processing Pipeline ({len(input_sheets)} inputs → {len(output_sheets)} outputs)')
        
        business_logic['business_processes'] = processes
        
        # Complexity assessment
        total_formulas = sum(sheet['formulas']['count'] for sheet in self.analysis_results.get('worksheets', {}).values())
        total_sheets = len(self.analysis_results.get('worksheets', {}))
        
        complexity = {
            'overall_complexity': 'High',
            'formula_density': total_formulas / max(total_sheets, 1),
            'sheet_interconnectivity': 'High' if total_sheets > 15 else 'Medium',
            'vba_complexity': self.analysis_results.get('vba_analysis', {}).get('estimated_complexity', 'Low'),
            'data_volume': 'Large' if any(sheet['data']['cell_count'] > 10000 
                                        for sheet in self.analysis_results.get('worksheets', {}).values()) else 'Medium'
        }
        
        business_logic['complexity_assessment'] = complexity
        
        self.analysis_results['business_logic'] = business_logic
        
        print("Core CLO Functions Identified:")
        for func in core_functions:
            print(f"  • {func}")
        
        print("\nBusiness Processes:")
        for process in processes:
            print(f"  • {process}")
        
        print(f"\nComplexity Assessment:")
        print(f"  • Overall Complexity: {complexity['overall_complexity']}")
        print(f"  • Formula Density: {complexity['formula_density']:.1f} formulas/sheet")
        print(f"  • VBA Complexity: {complexity['vba_complexity']}")
        print(f"  • Data Volume: {complexity['data_volume']}")
    
    def _analyze_data_relationships(self):
        """Analyze data relationships between worksheets"""
        print("\n5. DATA RELATIONSHIP ANALYSIS")
        print("-" * 50)
        
        relationships = {
            'sheet_dependencies': {},
            'data_sources': [],
            'calculation_engines': [],
            'output_generators': []
        }
        
        # Analyze formula references between sheets
        for sheet_name, sheet_data in self.analysis_results.get('worksheets', {}).items():
            dependencies = []
            
            # Look for sheet references in formulas
            for formula_sample in sheet_data['formulas']['samples']:
                formula = formula_sample.get('formula', '')
                
                # Find sheet references (e.g., 'SheetName'!A1 or SheetName!A1)
                sheet_refs = re.findall(r"'([^']+)'\!", formula)
                sheet_refs.extend(re.findall(r"([A-Za-z\s]+[A-Za-z])\!", formula.replace("'", "")))
                
                for ref_sheet in sheet_refs:
                    if ref_sheet != sheet_name and ref_sheet.strip():
                        dependencies.append(ref_sheet.strip())
            
            if dependencies:
                relationships['sheet_dependencies'][sheet_name] = list(set(dependencies))
        
        # Categorize sheets by function
        for sheet_name, sheet_data in self.analysis_results.get('worksheets', {}).items():
            purpose = sheet_data['business_indicators']['sheet_purpose']
            
            if 'Input' in purpose or 'Data' in purpose:
                relationships['data_sources'].append(sheet_name)
            elif 'Control' in purpose or 'Model' in purpose or 'Analysis' in purpose:
                relationships['calculation_engines'].append(sheet_name)
            elif 'Output' in purpose or 'Report' in purpose or 'Ranking' in purpose:
                relationships['output_generators'].append(sheet_name)
        
        self.analysis_results['data_relationships'] = relationships
        
        print(f"Data Sources: {len(relationships['data_sources'])}")
        for source in relationships['data_sources']:
            print(f"  • {source}")
        
        print(f"\nCalculation Engines: {len(relationships['calculation_engines'])}")
        for engine in relationships['calculation_engines']:
            print(f"  • {engine}")
        
        print(f"\nOutput Generators: {len(relationships['output_generators'])}")
        for output in relationships['output_generators']:
            print(f"  • {output}")
        
        print(f"\nSheet Dependencies:")
        for sheet, deps in relationships['sheet_dependencies'].items():
            if deps:
                print(f"  • {sheet} depends on: {', '.join(deps)}")
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE CLO SYSTEM ANALYSIS REPORT")
        print("=" * 80)
        
        # System Overview
        total_sheets = len(self.analysis_results.get('worksheets', {}))
        total_formulas = sum(sheet['formulas']['count'] for sheet in self.analysis_results.get('worksheets', {}).values())
        has_vba = self.analysis_results.get('vba_analysis', {}).get('has_vba', False)
        
        print(f"\nSYSTEM OVERVIEW:")
        print(f"  • File: {self.filepath.name}")
        print(f"  • Size: {self.filepath.stat().st_size / (1024*1024):.2f} MB")
        print(f"  • Total Worksheets: {total_sheets}")
        print(f"  • Total Formulas: {total_formulas}")
        print(f"  • Contains VBA: {'Yes' if has_vba else 'No'}")
        print(f"  • System Type: {self.analysis_results.get('business_logic', {}).get('system_type', 'CLO System')}")
        
        # Business Functions
        core_functions = self.analysis_results.get('business_logic', {}).get('core_functions', [])
        print(f"\nCORE BUSINESS FUNCTIONS:")
        for i, func in enumerate(core_functions, 1):
            print(f"  {i}. {func}")
        
        # Technical Architecture
        print(f"\nTECHNICAL ARCHITECTURE:")
        complexity = self.analysis_results.get('business_logic', {}).get('complexity_assessment', {})
        print(f"  • Complexity Level: {complexity.get('overall_complexity', 'Unknown')}")
        print(f"  • Formula Density: {complexity.get('formula_density', 0):.1f} per sheet")
        print(f"  • VBA Integration: {complexity.get('vba_complexity', 'None')}")
        print(f"  • Data Volume: {complexity.get('data_volume', 'Unknown')}")
        
        # Key Worksheets by Function
        print(f"\nKEY WORKSHEETS BY FUNCTION:")
        
        # Group sheets by purpose
        purpose_groups = {}
        for sheet_name, sheet_data in self.analysis_results.get('worksheets', {}).items():
            purpose = sheet_data['business_indicators']['sheet_purpose']
            if purpose not in purpose_groups:
                purpose_groups[purpose] = []
            purpose_groups[purpose].append(sheet_name)
        
        for purpose, sheets in purpose_groups.items():
            print(f"  • {purpose}: {len(sheets)} sheet(s)")
            for sheet in sheets[:3]:  # Show first 3
                print(f"    - {sheet}")
            if len(sheets) > 3:
                print(f"    - ... and {len(sheets)-3} more")
    
    def save_complete_analysis(self, output_path: str = None) -> str:
        """Save complete analysis to JSON file"""
        if not output_path:
            output_path = self.filepath.parent / f"{self.filepath.stem}_complete_analysis.json"
        
        # Ensure all data is JSON serializable
        json_safe_results = json.loads(json.dumps(self.analysis_results, default=str))
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_safe_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nComplete analysis saved to: {output_path}")
        return str(output_path)
    
    def generate_python_conversion_roadmap(self):
        """Generate detailed Python conversion roadmap"""
        print("\n" + "=" * 80)
        print("PYTHON CONVERSION ROADMAP")
        print("=" * 80)
        
        roadmap = {
            'project_scope': {},
            'architecture_design': {},
            'conversion_strategy': {},
            'implementation_phases': {},
            'risk_mitigation': {}
        }
        
        # Project Scope
        total_sheets = len(self.analysis_results.get('worksheets', {}))
        total_formulas = sum(sheet['formulas']['count'] for sheet in self.analysis_results.get('worksheets', {}).values())
        
        roadmap['project_scope'] = {
            'complexity_level': 'High',
            'estimated_duration': '16-24 weeks',
            'team_size_recommended': '4-6 developers',
            'worksheets_to_convert': total_sheets,
            'formulas_to_migrate': total_formulas,
            'has_vba_code': self.analysis_results.get('vba_analysis', {}).get('has_vba', False)
        }
        
        # Architecture Design
        roadmap['architecture_design'] = {
            'recommended_stack': [
                'Backend: Python + FastAPI/Flask',
                'Data Layer: PostgreSQL + SQLAlchemy',
                'Calculation Engine: NumPy + Pandas + SciPy',
                'Frontend: React.js + TypeScript',
                'API: REST with OpenAPI documentation',
                'Caching: Redis for performance',
                'Deployment: Docker + Kubernetes'
            ],
            'design_patterns': [
                'Layered Architecture (Data, Business Logic, API, UI)',
                'Repository Pattern for data access',
                'Strategy Pattern for different calculation methods',
                'Observer Pattern for real-time updates',
                'Factory Pattern for report generation'
            ]
        }
        
        # Conversion Strategy
        core_functions = self.analysis_results.get('business_logic', {}).get('core_functions', [])
        
        roadmap['conversion_strategy'] = {
            'phase_1_data_modeling': [
                f'Convert {total_sheets} worksheets to database schema',
                'Design normalized tables for assets, portfolios, ratings',
                'Create data validation and integrity constraints',
                'Implement data import/export functionality'
            ],
            'phase_2_business_logic': [
                f'Convert {total_formulas} Excel formulas to Python functions',
                'Implement CLO calculation algorithms',
                'Create scenario analysis engines',
                'Build compliance testing framework'
            ],
            'phase_3_user_interface': [
                'Design modern web-based UI',
                'Implement portfolio dashboard',
                'Create analysis and reporting views',
                'Build user management and permissions'
            ]
        }
        
        # Implementation Phases
        roadmap['implementation_phases'] = {
            'phase_1': {
                'name': 'Foundation & Data Architecture',
                'duration': '4-6 weeks',
                'deliverables': [
                    'Database schema design',
                    'Core data models',
                    'Data migration scripts',
                    'Basic API framework'
                ]
            },
            'phase_2': {
                'name': 'Core Business Logic',
                'duration': '6-8 weeks', 
                'deliverables': [
                    'Portfolio calculation engine',
                    'Risk analysis algorithms',
                    'Compliance testing framework',
                    'Scenario analysis tools'
                ]
            },
            'phase_3': {
                'name': 'Advanced Features',
                'duration': '4-6 weeks',
                'deliverables': [
                    'VBA logic conversion',
                    'Advanced analytics',
                    'Optimization algorithms',
                    'Performance tuning'
                ]
            },
            'phase_4': {
                'name': 'User Interface & Integration',
                'duration': '4-6 weeks',
                'deliverables': [
                    'Modern web interface',
                    'Dashboard and reporting',
                    'User authentication',
                    'System integration'
                ]
            }
        }
        
        # Print roadmap
        print("\nPROJECT SCOPE:")
        print(f"  • Complexity: {roadmap['project_scope']['complexity_level']}")
        print(f"  • Duration: {roadmap['project_scope']['estimated_duration']}")
        print(f"  • Team Size: {roadmap['project_scope']['team_size_recommended']}")
        print(f"  • Worksheets: {roadmap['project_scope']['worksheets_to_convert']}")
        print(f"  • Formulas: {roadmap['project_scope']['formulas_to_migrate']}")
        
        print("\nRECOMMENDED TECHNOLOGY STACK:")
        for tech in roadmap['architecture_design']['recommended_stack']:
            print(f"  • {tech}")
        
        print("\nIMPLEMENTATION PHASES:")
        for phase_key, phase_info in roadmap['implementation_phases'].items():
            print(f"  {phase_info['name']} ({phase_info['duration']}):")
            for deliverable in phase_info['deliverables']:
                print(f"    - {deliverable}")
        
        return roadmap

def main():
    """Main execution"""
    filepath = "TradeHypoPrelimv32.xlsm"
    
    if not Path(filepath).exists():
        print(f"Error: File '{filepath}' not found")
        return
    
    # Run comprehensive analysis
    analyzer = RobustCLOAnalyzer(filepath)
    results = analyzer.analyze_complete_system()
    
    # Save results
    output_file = analyzer.save_complete_analysis()
    
    # Generate conversion roadmap
    roadmap = analyzer.generate_python_conversion_roadmap()
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Complete analysis saved to: {output_file}")
    print("\nThis analysis provides comprehensive insights for converting the CLO Excel system to Python.")

if __name__ == "__main__":
    main()