# RAG System Deprecation Notice

## ⚠️ DEPRECATED: Basic RAG System (iep_generator.py)

**Effective Date**: July 16, 2025  
**Replacement**: Enhanced Metadata-Aware RAG System (`metadata_aware_iep_generator.py`)

---

## Summary

The basic RAG system (`src/rag/iep_generator.py`) has been **deprecated** in favor of the enhanced metadata-aware system that provides:

- **Quality-assured content retrieval** with 4-dimensional assessment
- **Section-specific evidence collection** for targeted IEP generation  
- **Source attribution and confidence scoring** for transparency
- **Metadata-intelligent search** with filtering and ranking

---

## Migration Status

### ✅ COMPLETED
- **Advanced IEP Router**: Updated to use `MetadataAwareIEPGenerator`
- **IEP Service**: Enhanced with dual-mode support (enhanced + legacy fallback)
- **Vector Store**: Upgraded to `EnhancedVectorStore` with metadata capabilities
- **Assessment Pipeline Integration**: Now routes through enhanced RAG system

### 📋 ENDPOINTS AFFECTED
- **`/api/v1/ieps/advanced/create-with-rag`**: Now uses enhanced RAG system
- **`/api/v1/ieps/advanced/similar-ieps/{student_id}`**: Uses metadata-aware search
- **Assessment Pipeline**: Document AI → Enhanced RAG → Quality-assured IEPs

---

## Operational Changes

### Before (Deprecated System)
```
Document Text → Basic Vector Search → Gemini → Generated IEP
```

### After (Enhanced System)  
```
Document → Metadata Extraction → Quality Assessment → Section-Specific Evidence Collection → Enhanced Context → Gemini → Validated IEP + Evidence Metadata
```

---

## Benefits of Enhanced System

1. **Evidence-Based Generation**: IEPs now include source attribution for all content
2. **Quality Assurance**: 4-dimensional quality assessment ensures professional standards
3. **Targeted Retrieval**: Section-specific search improves content relevance
4. **Transparency**: Complete evidence chains build educator trust
5. **Confidence Scoring**: Quality metrics help identify areas needing review

---

## Legacy Support

The old system remains available as a **fallback** in case of enhanced system failures:

```python
# Fallback mechanism in advanced_iep_router.py
try:
    enhanced_vector_store = EnhancedVectorStore(...)
    metadata_aware_iep_generator = MetadataAwareIEPGenerator(...)
except Exception as e:
    # Fallback to legacy system
    vector_store = VectorStore(...)
    metadata_aware_iep_generator = IEPGenerator(...)  # Legacy fallback
```

---

## Removal Timeline

- **Phase 1** (Current): Enhanced system active, legacy as fallback
- **Phase 2** (After validation): Remove legacy fallback code
- **Phase 3** (Future): Complete removal of deprecated files

---

## Files Affected

### Deprecated Files
- `src/rag/iep_generator.py` - Basic RAG generator
- `src/vector_store.py` - Simple vector store

### New Enhanced Files
- `src/rag/metadata_aware_iep_generator.py` - Enhanced RAG generator
- `src/vector_store_enhanced.py` - Metadata-aware vector store
- `src/schemas/rag_metadata_schemas.py` - Comprehensive metadata schemas
- `src/services/document_metadata_extractor.py` - Intelligent metadata extraction

---

## For Developers

If you're working with the RAG system:

1. **Use Enhanced System**: Import from `metadata_aware_iep_generator`
2. **Update Dependencies**: Use `EnhancedVectorStore` instead of `VectorStore`
3. **Leverage Metadata**: Take advantage of quality filtering and source attribution
4. **Review Logs**: Enhanced system provides detailed evidence collection logging

---

## Testing Enhanced Integration

```bash
# Test enhanced RAG with assessment pipeline
curl -X POST "http://localhost:8005/api/v1/ieps/advanced/create-with-rag" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "c6f74363-c1fb-4b0f-bd6b-0ae5c8a6f826",
    "template_id": "3f2f2152-6758-425e-a3ed-3f4c2fd8afb8",
    "academic_year": "2025-2026"
  }'

# Response should include:
# - generation_method: "enhanced_rag_metadata_aware"
# - evidence_metadata: {...}
# - quality_score: 0.xxx
# - confidence_scores: {...}
```

---

*This deprecation notice ensures smooth transition to the enhanced RAG system while maintaining backward compatibility during the migration period.*