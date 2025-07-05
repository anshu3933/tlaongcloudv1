# Integrated IEP Generation System Design

## Executive Summary

This design integrates document upload capabilities with structured data collection to eliminate content regurgitation and generate professional, personalized IEPs. The system extracts structured data from uploaded documents and uses checkboxes/scales instead of prose fields.

## Core Problem Statement

Current system issues:
- 130+ text areas that collect prose, which gets regurgitated into output
- Test shows 85-90% regurgitation despite claims of 0%
- Users are writing IEP content instead of providing data
- AI copy-pastes input instead of generating original content

## Design Principles

1. **Collect Facts, Not Prose**: Use structured inputs (scales, checkboxes, dropdowns)
2. **Extract, Don't Transcribe**: AI extracts data points from documents
3. **Context, Not Content**: Input is reference material, not text to copy
4. **Evidence-Based Generation**: Match strategies to needs using research
5. **Professional Standards**: Generate SMART goals with measurable criteria

## System Architecture

### Phase 1: Document Intelligence Layer

```typescript
interface DocumentProcessor {
  // Accepts multiple document types
  supportedFormats: ['pdf', 'docx', 'jpg', 'png'];
  
  // Document categories
  documentTypes: {
    previousIEP: 'Previous IEP documents',
    assessment: 'Psychological/educational assessments',
    reportCard: 'Progress reports and grades',
    teacherNotes: 'Observation notes and anecdotal records',
    medical: 'Medical reports and diagnoses'
  };
  
  // Extraction pipeline
  extractionSteps: [
    'OCR if needed',
    'Document classification',
    'Section identification',
    'Data point extraction',
    'Confidence scoring',
    'Human review flagging'
  ];
}
```

### Phase 2: Structured Data Collection

Replace 130+ text areas with:

```typescript
interface StructuredDataForm {
  // Student Profile (Facts only)
  studentProfile: {
    name: string;
    dateOfBirth: Date;
    grade: Dropdown<K-12>;
    primaryDisability: Dropdown<DisabilityCategories>;
    secondaryDisabilities: MultiSelect<DisabilityCategories>;
    englishProficiency: Scale<1-5>;
    attendanceRate: Percentage;
  };
  
  // Academic Performance (Measurable data)
  academicData: {
    reading: {
      currentLevel: GradeLevel;
      wpmFluency: number;
      comprehensionPercentile: number;
      specificChallenges: Checkboxes<[
        'Decoding',
        'Fluency',
        'Vocabulary',
        'Main idea',
        'Inference',
        'Critical analysis'
      ]>;
    };
    
    math: {
      currentLevel: GradeLevel;
      computationAccuracy: Percentage;
      problemSolvingScore: Percentile;
      specificChallenges: Checkboxes<[
        'Number sense',
        'Basic operations',
        'Fractions/decimals',
        'Word problems',
        'Algebra concepts',
        'Geometry'
      ]>;
    };
    
    writing: {
      sentenceStructure: Scale<1-5>;
      paragraphOrganization: Scale<1-5>;
      grammarAccuracy: Percentage;
      specificChallenges: Checkboxes<[
        'Handwriting',
        'Spelling',
        'Sentence formation',
        'Paragraph structure',
        'Essay organization',
        'Revision skills'
      ]>;
    };
  };
  
  // Behavioral & Social (Observable metrics)
  behavioralData: {
    attentionSpan: {
      sustainedMinutes: number;
      requiresBreaks: boolean;
      breakFrequency: Dropdown<['Every 15 min', 'Every 30 min', 'Hourly']>;
    };
    
    socialSkills: {
      peerInteraction: Scale<1-5>;
      adultInteraction: Scale<1-5>;
      conflictResolution: Scale<1-5>;
      specificConcerns: Checkboxes<[
        'Initiating interactions',
        'Maintaining friendships',
        'Reading social cues',
        'Managing emotions',
        'Following social rules'
      ]>;
    };
    
    behaviorPatterns: {
      frequency: Map<BehaviorType, FrequencyScale>;
      triggers: MultiSelect<CommonTriggers>;
      successfulInterventions: Checkboxes<EvidenceBasedInterventions>;
    };
  };
  
  // Learning Preferences (Not prose)
  learningProfile: {
    primaryModality: Radio<['Visual', 'Auditory', 'Kinesthetic', 'Mixed']>;
    bestTimeOfDay: Radio<['Morning', 'Midday', 'Afternoon']>;
    preferredGrouping: Radio<['Individual', 'Pairs', 'Small group', 'Whole class']>;
    motivators: Checkboxes<CommonMotivators>;
    sensoryNeeds: Checkboxes<SensoryConsiderations>;
  };
  
  // Support History (What works)
  supportData: {
    currentAccommodations: {
      [accommodation: string]: {
        effectiveness: Scale<1-5>;
        frequency: Dropdown<FrequencyOptions>;
        setting: MultiSelect<Settings>;
      };
    };
    
    previousInterventions: {
      [intervention: string]: {
        duration: number; // weeks
        effectiveness: Scale<1-5>;
        discontinued: boolean;
        reason: Dropdown<DiscontinuationReasons>;
      };
    };
  };
}
```

### Phase 3: AI Extraction Pipeline

```typescript
interface ExtractionPipeline {
  // Step 1: Document Analysis
  analyzeDocument(file: File): {
    documentType: DocumentType;
    sections: Section[];
    confidence: number;
    extractedData: DataPoints[];
  };
  
  // Step 2: Data Structuring
  structureData(extractedData: DataPoints[]): {
    // Maps to structured form fields
    academicLevels: Map<Subject, GradeLevel>;
    assessmentScores: Map<Test, Score>;
    behaviorFrequencies: Map<Behavior, Frequency>;
    previousGoals: Goal[];
    progressData: ProgressMetric[];
  };
  
  // Step 3: Validation & Review
  validateExtraction(data: StructuredData): {
    highConfidence: DataPoint[];
    needsReview: DataPoint[];
    missing: RequiredField[];
    conflicts: DataConflict[];
  };
  
  // Step 4: Form Pre-population
  populateForm(validatedData: StructuredData): {
    prefilledFields: FormFields;
    reviewFlags: ReviewItem[];
    alternativeValues: Map<Field, Alternative[]>;
  };
}
```

### Phase 4: Backend Transformation Layer

```python
class IEPContentGenerator:
    """Transforms structured data into professional IEP content"""
    
    def __init__(self):
        self.evidence_base = EvidenceBasedStrategyMatcher()
        self.goal_generator = SMARTGoalGenerator()
        self.service_recommender = ServiceRecommendationEngine()
    
    def transform_to_context(self, structured_data: Dict) -> Dict:
        """Convert form data to AI context (not content)"""
        return {
            "student_profile": self._extract_profile_facts(structured_data),
            "performance_data": self._extract_performance_metrics(structured_data),
            "effective_supports": self._extract_what_works(structured_data),
            "challenge_areas": self._extract_specific_needs(structured_data),
            "NOT_FOR_COPYING": "Generate original content based on these facts"
        }
    
    def generate_with_alternatives(self, context: Dict) -> Dict:
        """Generate multiple options with rationales"""
        return {
            "goals": [
                {
                    "primary": self._generate_goal(need),
                    "alternatives": self._generate_goal_alternatives(need),
                    "rationale": self._explain_goal_choice(need),
                    "research_base": self._cite_evidence(need)
                }
                for need in context["challenge_areas"]
            ],
            "services": self._match_services_to_needs(context),
            "accommodations": self._recommend_accommodations(context)
        }
    
    def enforce_quality_rules(self, prompt: str) -> str:
        """Add strict rules to prevent regurgitation"""
        return f"""
        {prompt}
        
        CRITICAL RULES:
        1. DO NOT copy or paraphrase ANY text from the input
        2. Generate ORIGINAL professional language
        3. Use input as DATA POINTS only, not sentences to reuse
        4. Create specific, measurable criteria not found in input
        5. If you find yourself writing something similar to input, STOP and rephrase completely
        
        QUALITY REQUIREMENTS:
        - Use professional special education terminology
        - Include specific measurement criteria (80%, 4/5 trials, etc.)
        - Reference evidence-based practices
        - Write in future-focused language ("will demonstrate", "will achieve")
        - Avoid vague terms ("various", "different", "appropriate")
        """
```

### Phase 5: Quality Validation System

```python
class QualityValidator:
    """Ensures generated content meets professional standards"""
    
    def validate_output(self, input_data: Dict, output_content: Dict) -> ValidationResult:
        checks = {
            "regurgitation": self._check_copying(input_data, output_content),
            "professional_language": self._check_terminology(output_content),
            "measurability": self._check_smart_criteria(output_content),
            "specificity": self._check_vague_language(output_content),
            "completeness": self._check_required_sections(output_content)
        }
        
        return ValidationResult(
            passed=all(check.passed for check in checks.values()),
            issues=[check.message for check in checks.values() if not check.passed],
            suggestions=self._generate_improvement_suggestions(checks)
        )
    
    def _check_copying(self, input_data: Dict, output: Dict) -> Check:
        """Detect copy-paste from input"""
        input_phrases = self._extract_phrases(input_data, min_length=4)
        output_text = self._flatten_to_text(output)
        
        copied_phrases = [
            phrase for phrase in input_phrases 
            if phrase.lower() in output_text.lower()
        ]
        
        copy_percentage = len(copied_phrases) / len(input_phrases) * 100
        
        return Check(
            passed=copy_percentage < 10,
            score=copy_percentage,
            message=f"Found {copy_percentage:.1f}% copied content"
        )
```

## User Interface Design

### Document Upload Interface

```typescript
interface DocumentUploadUI {
  // Drag-and-drop zone
  uploadZone: {
    acceptedFormats: string[];
    maxFileSize: number;
    multipleFiles: boolean;
    categorization: Required;
  };
  
  // Document preview
  documentPreview: {
    thumbnail: boolean;
    extractedDataHighlights: boolean;
    confidenceIndicators: boolean;
    editableFields: boolean;
  };
  
  // Extraction status
  processingStatus: {
    stage: 'Uploading' | 'Analyzing' | 'Extracting' | 'Validating' | 'Complete';
    progressBar: boolean;
    extractedItemCount: number;
    reviewRequiredCount: number;
  };
}
```

### Structured Form Interface

```typescript
interface StructuredFormUI {
  // Progress indicator
  progressBar: {
    sections: string[];
    completionPercentage: number;
    requiredFieldsRemaining: number;
  };
  
  // Smart sections
  sections: {
    academicPerformance: {
      layout: 'Grid';
      inputs: 'Scales, percentages, checkboxes';
      validation: 'Real-time';
      help: 'Contextual tooltips';
    };
    
    behavioralProfile: {
      layout: 'Frequency matrices';
      inputs: 'Radio buttons, sliders';
      visualization: 'Charts showing patterns';
    };
    
    supportEffectiveness: {
      layout: 'Effectiveness grid';
      inputs: 'Star ratings, toggles';
      history: 'Timeline view';
    };
  };
  
  // AI assistance
  aiFeatures: {
    fieldSuggestions: boolean;
    conflictDetection: boolean;
    completionAssistance: boolean;
    evidenceLinks: boolean;
  };
}
```

## Implementation Phases

### Phase 1: Document Processing (Week 1-2)
- Implement document upload API
- Create PDF text extraction
- Build AI extraction prompts
- Design extraction data models

### Phase 2: Form Redesign (Week 2-3)
- Replace text areas with structured inputs
- Create new form components
- Implement form validation
- Add progress tracking

### Phase 3: Backend Integration (Week 3-4)
- Create transformation layer
- Update prompt engineering
- Implement quality validation
- Add alternative generation

### Phase 4: Testing & Refinement (Week 4-5)
- Test with real documents
- Measure regurgitation rates
- Refine extraction accuracy
- Optimize user flow

## Success Metrics

1. **Regurgitation Rate**: < 10% (down from 85-90%)
2. **Data Extraction Accuracy**: > 85% from uploaded documents
3. **Form Completion Time**: < 20 minutes (from 45+ minutes)
4. **SMART Goal Compliance**: 100% of generated goals
5. **Professional Terminology**: > 15 special ed terms per IEP
6. **User Satisfaction**: > 4.5/5 rating

## Risk Mitigation

1. **Poor OCR Quality**: Provide manual override options
2. **Incorrect Extraction**: Human review flags for low-confidence items
3. **Missing Data**: Smart defaults based on disability category
4. **Resistance to Change**: Gradual rollout with training
5. **Technical Complexity**: Modular implementation approach

## Conclusion

This integrated design solves the fundamental problem of content regurgitation by:
1. Extracting structured data from documents instead of copying text
2. Collecting facts through checkboxes/scales instead of prose
3. Using data as context for generation, not content to copy
4. Generating multiple professional alternatives with rationales
5. Validating quality to ensure original, professional output

The result will be IEPs that are truly personalized, professionally written, and compliant with special education standards.