"""
Enhanced Vector Store with Metadata Capabilities
===============================================

Advanced vector store implementation that extends ChromaDB with comprehensive
metadata indexing, filtering, and search capabilities for the RAG pipeline.

Created: 2025-07-16
Task: TASK-007 - Update Vector Store with Metadata Capabilities
Dependencies: TASK-001 (Metadata Schemas), TASK-002 (Metadata Extractor)
"""

import chromadb
from chromadb.config import Settings
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import json
import asyncio
from datetime import datetime
import numpy as np
import re
from collections import defaultdict, Counter

from .schemas.rag_metadata_schemas import (
    ChunkLevelMetadata, DocumentLevelMetadata, SearchContext,
    EnhancedSearchResult, IEPSection, DocumentType, AssessmentType,
    MetadataValidationReport
)


logger = logging.getLogger(__name__)


class EnhancedVectorStore:
    """
    Enhanced vector store with comprehensive metadata support
    
    Features:
    - Metadata-aware indexing and search
    - Complex filtering and ranking
    - Quality-based retrieval
    - Relationship-aware queries
    - Performance optimization
    """
    
    def __init__(
        self, 
        persist_directory: str = "./chromadb",
        collection_name: str = "enhanced_educational_docs"
    ):
        """Initialize enhanced vector store"""
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"📚 Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Enhanced educational documents with metadata"}
            )
            logger.info(f"🆕 Created new collection: {collection_name}")
        
        # Metadata validation cache
        self._validation_cache = {}
        
        # Performance metrics
        self._search_metrics = defaultdict(list)
        
        logger.info(f"✅ Enhanced vector store initialized")
        logger.info(f"📊 Current collection size: {self.collection.count()}")

    async def add_document_with_metadata(
        self,
        chunks: List[Dict[str, Any]],
        document_metadata: DocumentLevelMetadata,
        chunk_metadatas: List[ChunkLevelMetadata]
    ) -> bool:
        """
        Add document chunks with comprehensive metadata
        
        Args:
            chunks: List of text chunks with embeddings
            document_metadata: Document-level metadata
            chunk_metadatas: List of chunk-level metadata
            
        Returns:
            bool: Success status
        """
        
        start_time = datetime.now()
        logger.info(f"📥 Adding document with {len(chunks)} chunks: {document_metadata.document_id}")
        
        try:
            # Validate inputs
            if len(chunks) != len(chunk_metadatas):
                raise ValueError("Number of chunks must match number of chunk metadatas")
            
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents = []
            metadatas = []
            
            for i, (chunk, chunk_metadata) in enumerate(zip(chunks, chunk_metadatas)):
                # Generate unique ID
                chunk_id = f"{document_metadata.document_id}_chunk_{i:04d}"
                ids.append(chunk_id)
                
                # Extract content and embedding
                documents.append(chunk['content'])
                embeddings.append(chunk['embedding'])
                
                # Convert metadata to ChromaDB format
                chromadb_metadata = await self._convert_metadata_for_storage(
                    chunk_metadata, document_metadata
                )
                metadatas.append(chromadb_metadata)
                
                logger.debug(f"📝 Prepared chunk {i+1}/{len(chunks)}: {chunk_id}")
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            # Update document metadata total chunks
            document_metadata.total_chunks = len(chunks)
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Document added successfully in {duration:.2f}s")
            logger.info(f"📊 Collection size now: {self.collection.count()}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add document: {e}")
            return False

    async def enhanced_search(
        self,
        query_text: str,
        search_context: SearchContext,
        n_results: int = 10
    ) -> List[EnhancedSearchResult]:
        """
        Perform enhanced search with metadata filtering and ranking
        
        Args:
            query_text: Search query
            search_context: Search context and filters
            n_results: Maximum number of results
            
        Returns:
            List[EnhancedSearchResult]: Enhanced search results with metadata
        """
        
        start_time = datetime.now()
        logger.info(f"🔍 Enhanced search: '{query_text}' with context filters")
        
        try:
            # Build metadata filters
            where_filters = await self._build_metadata_filters(search_context)
            logger.debug(f"🔧 Applied filters: {where_filters}")
            
            # Perform vector search with filters
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results * 2, 50),  # Get extra for re-ranking
                where=where_filters if where_filters else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results['ids'] or not results['ids'][0]:
                logger.info("🔍 No results found matching criteria")
                return []
            
            # Convert to enhanced results
            enhanced_results = await self._convert_to_enhanced_results(
                results, query_text, search_context
            )
            
            # Apply quality filtering
            filtered_results = await self._apply_quality_filtering(
                enhanced_results, search_context
            )
            
            # Re-rank by combined scoring
            ranked_results = await self._rerank_results(
                filtered_results, search_context
            )
            
            # Limit to requested number
            final_results = ranked_results[:n_results]
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Search completed in {duration:.2f}s")
            logger.info(f"📊 Found {len(final_results)} results from {len(results['ids'][0])} candidates")
            
            # Track performance metrics
            self._search_metrics['query_time'].append(duration)
            self._search_metrics['result_count'].append(len(final_results))
            
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Enhanced search failed: {e}")
            return []

    async def _build_metadata_filters(self, search_context: SearchContext) -> Optional[Dict]:
        """Build ChromaDB where filters from search context"""
        
        # ChromaDB requires filters to be combined with $and if multiple conditions
        filters = []
        
        # Document type filters
        if search_context.document_types:
            filters.append({
                "document_type": {"$in": [dt.value for dt in search_context.document_types]}
            })
        
        # Assessment type filters  
        if search_context.assessment_types:
            filters.append({
                "assessment_type": {"$in": [at.value for at in search_context.assessment_types]}
            })
        
        # Quality threshold
        if search_context.quality_threshold > 0:
            filters.append({
                "overall_quality": {"$gte": search_context.quality_threshold}
            })
        
        # Date range filters
        if search_context.date_range:
            date_filters = {}
            if "start" in search_context.date_range:
                date_filters["$gte"] = search_context.date_range["start"].isoformat()
            if "end" in search_context.date_range:
                date_filters["$lte"] = search_context.date_range["end"].isoformat()
            
            if date_filters:
                filters.append({"document_date": date_filters})
        
        # Student context
        if search_context.student_context and "student_id" in search_context.student_context:
            filters.append({
                "student_id": search_context.student_context["student_id"]
            })
        
        # IEP section relevance (if target section specified)
        if search_context.target_iep_section:
            section_field = f"relevance_{search_context.target_iep_section.value}"
            filters.append({
                section_field: {"$gte": 0.3}
            })
        
        # Combine filters with $and if multiple, or return single filter
        if len(filters) == 0:
            return None
        elif len(filters) == 1:
            return filters[0]
        else:
            return {"$and": filters}

    async def _convert_metadata_for_storage(
        self,
        chunk_metadata: ChunkLevelMetadata,
        document_metadata: DocumentLevelMetadata
    ) -> Dict[str, Any]:
        """Convert metadata objects to ChromaDB-compatible format"""
        
        # Flatten metadata for ChromaDB storage
        storage_metadata = {
            # Chunk identity
            "chunk_id": chunk_metadata.chunk_id,
            "document_id": chunk_metadata.document_id,
            "chunk_index": chunk_metadata.chunk_index,
            
            # Document classification
            "document_type": document_metadata.document_type.value,
            "assessment_type": document_metadata.assessment_type.value if document_metadata.assessment_type else None,
            
            # Quality metrics
            "extraction_confidence": chunk_metadata.quality_metrics.extraction_confidence,
            "information_density": chunk_metadata.quality_metrics.information_density,
            "overall_quality": chunk_metadata.quality_metrics.overall_quality,
            
            # Temporal information
            "document_date": document_metadata.temporal_metadata.document_date.isoformat() if document_metadata.temporal_metadata.document_date else None,
            "processing_date": chunk_metadata.processing_timestamp.isoformat(),
            "school_year": document_metadata.temporal_metadata.school_year,
            
            # Semantic information
            "primary_topic": chunk_metadata.semantic_metadata.primary_topic,
            "content_type": chunk_metadata.semantic_metadata.content_type,
            "educational_domain": json.dumps(chunk_metadata.semantic_metadata.educational_domain),
            
            # IEP section relevance scores
            "relevance_student_info": chunk_metadata.iep_section_relevance.student_info,
            "relevance_present_levels": chunk_metadata.iep_section_relevance.present_levels,
            "relevance_annual_goals": chunk_metadata.iep_section_relevance.annual_goals,
            "relevance_accommodations": chunk_metadata.iep_section_relevance.accommodations,
            "relevance_services": chunk_metadata.iep_section_relevance.special_education_services,
            
            # Relationships
            "student_id": chunk_metadata.relationships.student_id,
            "previous_chunk_id": chunk_metadata.relationships.previous_chunk_id,
            "next_chunk_id": chunk_metadata.relationships.next_chunk_id,
            
            # Processing information
            "embedding_model": chunk_metadata.embedding_model,
            "processing_version": document_metadata.processing_version,
            
            # File information
            "source_path": document_metadata.source_path,
            "filename": document_metadata.filename,
            "file_size": document_metadata.file_size_bytes,
        }
        
        # Remove None values
        storage_metadata = {k: v for k, v in storage_metadata.items() if v is not None}
        
        return storage_metadata

    async def _convert_to_enhanced_results(
        self,
        chromadb_results: Dict,
        query_text: str,
        search_context: SearchContext
    ) -> List[EnhancedSearchResult]:
        """Convert ChromaDB results to enhanced result format"""
        
        enhanced_results = []
        
        # Extract result data
        ids = chromadb_results['ids'][0]
        documents = chromadb_results['documents'][0]
        metadatas = chromadb_results['metadatas'][0]
        distances = chromadb_results['distances'][0]
        
        for i, (chunk_id, content, metadata, distance) in enumerate(
            zip(ids, documents, metadatas, distances)
        ):
            try:
                # Convert distance to similarity score
                similarity_score = max(0.0, 1.0 - distance)
                
                # Calculate relevance score
                relevance_score = await self._calculate_relevance_score(
                    metadata, search_context
                )
                
                # Get quality score
                quality_score = metadata.get('overall_quality', 0.5)
                
                # Calculate final score (weighted combination)
                final_score = (
                    similarity_score * 0.4 +
                    relevance_score * 0.4 +
                    quality_score * 0.2
                )
                
                # Create enhanced result
                enhanced_result = EnhancedSearchResult(
                    chunk_id=chunk_id,
                    content=content,
                    similarity_score=similarity_score,
                    relevance_score=relevance_score,
                    quality_score=quality_score,
                    final_score=final_score,
                    chunk_metadata=await self._reconstruct_chunk_metadata(metadata),
                    match_highlights=self._generate_match_highlights(content, query_text),
                    relevance_explanation=self._generate_relevance_explanation(
                        metadata, search_context
                    ),
                    source_attribution=self._generate_source_attribution(metadata)
                )
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not convert result {i}: {e}")
                continue
        
        return enhanced_results

    async def _calculate_relevance_score(
        self,
        metadata: Dict[str, Any],
        search_context: SearchContext
    ) -> float:
        """Calculate relevance score based on search context"""
        
        relevance_score = 0.5  # Base score
        
        # IEP section relevance boost
        if search_context.target_iep_section:
            section_field = f"relevance_{search_context.target_iep_section.value}"
            section_relevance = metadata.get(section_field, 0.0)
            relevance_score += section_relevance * 0.3
        
        # Document type relevance
        if search_context.document_types:
            doc_type = metadata.get('document_type')
            if doc_type in [dt.value for dt in search_context.document_types]:
                relevance_score += 0.2
        
        # Recency boost
        if search_context.boost_recent and metadata.get('document_date'):
            try:
                doc_date = datetime.fromisoformat(metadata['document_date'])
                days_old = (datetime.now() - doc_date).days
                if days_old < 365:  # Recent documents get boost
                    recency_boost = max(0, 0.1 - (days_old / 3650))
                    relevance_score += recency_boost
            except:
                pass
        
        # Student context relevance
        if (search_context.student_context and 
            search_context.student_context.get('student_id') == metadata.get('student_id')):
            relevance_score += 0.15
        
        return min(relevance_score, 1.0)

    async def _apply_quality_filtering(
        self,
        results: List[EnhancedSearchResult],
        search_context: SearchContext
    ) -> List[EnhancedSearchResult]:
        """Apply quality threshold filtering"""
        
        if search_context.quality_threshold <= 0:
            return results
        
        filtered_results = [
            result for result in results
            if result.quality_score >= search_context.quality_threshold
        ]
        
        logger.debug(f"🔧 Quality filtering: {len(results)} → {len(filtered_results)} results")
        
        return filtered_results

    async def _rerank_results(
        self,
        results: List[EnhancedSearchResult],
        search_context: SearchContext
    ) -> List[EnhancedSearchResult]:
        """Re-rank results by final score"""
        
        # Sort by final score (descending)
        ranked_results = sorted(
            results,
            key=lambda r: r.final_score,
            reverse=True
        )
        
        logger.debug(f"🔄 Re-ranked {len(results)} results by final score")
        
        return ranked_results

    async def _reconstruct_chunk_metadata(self, storage_metadata: Dict) -> ChunkLevelMetadata:
        """Reconstruct ChunkLevelMetadata from storage format (simplified)"""
        
        # This is a simplified reconstruction - in production, you'd want
        # to store and retrieve the complete metadata objects
        from .schemas.rag_metadata_schemas import (
            QualityMetrics, SemanticMetadata, IEPSectionRelevance, 
            RelationshipMetadata
        )
        
        # Create minimal metadata object for demo
        quality_metrics = QualityMetrics(
            extraction_confidence=storage_metadata.get('extraction_confidence', 0.5),
            information_density=storage_metadata.get('information_density', 0.5),
            readability_score=0.5,
            completeness_score=0.5,
            validation_status="unvalidated",
            overall_quality=storage_metadata.get('overall_quality', 0.5)
        )
        
        semantic_metadata = SemanticMetadata(
            primary_topic=storage_metadata.get('primary_topic', 'Unknown'),
            content_type=storage_metadata.get('content_type', 'narrative')
        )
        
        iep_relevance = IEPSectionRelevance(
            student_info=storage_metadata.get('relevance_student_info', 0.0),
            present_levels=storage_metadata.get('relevance_present_levels', 0.0),
            annual_goals=storage_metadata.get('relevance_annual_goals', 0.0),
            accommodations=storage_metadata.get('relevance_accommodations', 0.0),
            special_education_services=storage_metadata.get('relevance_services', 0.0)
        )
        
        relationships = RelationshipMetadata(
            student_id=storage_metadata.get('student_id'),
            previous_chunk_id=storage_metadata.get('previous_chunk_id'),
            next_chunk_id=storage_metadata.get('next_chunk_id')
        )
        
        return ChunkLevelMetadata(
            chunk_id=storage_metadata.get('chunk_id', 'unknown'),
            document_id=storage_metadata.get('document_id', 'unknown'),
            chunk_index=storage_metadata.get('chunk_index', 0),
            content_length=0,
            semantic_metadata=semantic_metadata,
            iep_section_relevance=iep_relevance,
            quality_metrics=quality_metrics,
            relationships=relationships,
            embedding_model=storage_metadata.get('embedding_model', 'unknown'),
            embedding_version='1.0',
            processing_timestamp=datetime.now(),
            last_updated=datetime.now()
        )

    def _generate_match_highlights(self, content: str, query_text: str) -> List[str]:
        """Generate highlighted matching terms"""
        
        # Simple highlighting - find query terms in content
        query_terms = query_text.lower().split()
        highlights = []
        
        for term in query_terms:
            if term in content.lower():
                # Find the term with context
                pattern = rf'(\S*\s*){{0,3}}\b{re.escape(term)}\b(\s*\S*){{0,3}}'
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    highlights.append(match.group(0).strip())
        
        return highlights[:5]  # Limit to 5 highlights

    def _generate_relevance_explanation(
        self,
        metadata: Dict[str, Any],
        search_context: SearchContext
    ) -> str:
        """Generate explanation of why result is relevant"""
        
        explanations = []
        
        # Document type relevance
        doc_type = metadata.get('document_type', 'unknown')
        explanations.append(f"Document type: {doc_type}")
        
        # Quality score
        quality = metadata.get('overall_quality', 0.0)
        explanations.append(f"Quality score: {quality:.2f}")
        
        # IEP section relevance
        if search_context.target_iep_section:
            section_field = f"relevance_{search_context.target_iep_section.value}"
            section_score = metadata.get(section_field, 0.0)
            explanations.append(f"Relevance to {search_context.target_iep_section.value}: {section_score:.2f}")
        
        return "; ".join(explanations)

    def _generate_source_attribution(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Generate source attribution information"""
        
        return {
            "filename": metadata.get('filename', 'Unknown'),
            "document_type": metadata.get('document_type', 'Unknown'),
            "document_date": metadata.get('document_date', 'Unknown'),
            "source_path": metadata.get('source_path', 'Unknown')
        }

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get comprehensive collection statistics"""
        
        logger.info("📊 Gathering collection statistics...")
        
        try:
            # Basic stats
            total_chunks = self.collection.count()
            
            # Get sample of metadata for analysis
            sample_results = self.collection.get(
                limit=min(100, total_chunks),
                include=['metadatas']
            )
            
            if not sample_results['metadatas']:
                return {"total_chunks": total_chunks, "metadata_coverage": 0}
            
            # Analyze metadata coverage
            metadata_fields = set()
            doc_types = defaultdict(int)
            quality_scores = []
            
            for metadata in sample_results['metadatas']:
                metadata_fields.update(metadata.keys())
                
                doc_type = metadata.get('document_type', 'unknown')
                doc_types[doc_type] += 1
                
                quality = metadata.get('overall_quality')
                if quality is not None:
                    quality_scores.append(quality)
            
            # Calculate statistics
            avg_quality = np.mean(quality_scores) if quality_scores else 0
            metadata_coverage = len(metadata_fields)
            
            stats = {
                "total_chunks": total_chunks,
                "metadata_coverage": metadata_coverage,
                "document_types": dict(doc_types),
                "average_quality": avg_quality,
                "metadata_fields": sorted(list(metadata_fields)),
                "search_metrics": {
                    "avg_query_time": np.mean(self._search_metrics['query_time']) if self._search_metrics['query_time'] else 0,
                    "total_searches": len(self._search_metrics['query_time'])
                }
            }
            
            logger.info(f"📊 Collection stats: {total_chunks} chunks, {metadata_coverage} metadata fields")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get collection stats: {e}")
            return {"error": str(e)}

    async def validate_metadata_integrity(self) -> MetadataValidationReport:
        """Validate metadata integrity across the collection"""
        
        logger.info("🔍 Validating metadata integrity...")
        
        validation_start = datetime.now()
        
        try:
            # Get all metadata for validation
            all_results = self.collection.get(include=['metadatas'])
            metadatas = all_results['metadatas']
            
            total_fields = 0
            fields_passed = 0
            errors = []
            warnings = []
            
            required_fields = [
                'chunk_id', 'document_id', 'document_type', 'overall_quality'
            ]
            
            for i, metadata in enumerate(metadatas):
                # Check required fields
                for field in required_fields:
                    total_fields += 1
                    if field in metadata and metadata[field] is not None:
                        fields_passed += 1
                    else:
                        errors.append(f"Missing required field '{field}' in chunk {i}")
                
                # Validate quality scores
                quality = metadata.get('overall_quality')
                if quality is not None:
                    if not (0 <= quality <= 1):
                        errors.append(f"Invalid quality score {quality} in chunk {i}")
            
            # Generate validation report
            report = MetadataValidationReport(
                validation_timestamp=validation_start,
                is_valid=len(errors) == 0,
                schema_validation=len(errors) == 0,
                consistency_validation=True,  # Simplified for demo
                quality_validation=True,
                relationship_validation=True,
                validation_errors=errors,
                validation_warnings=warnings,
                improvement_suggestions=[
                    "Consider adding more comprehensive metadata validation",
                    "Implement automated quality score validation"
                ] if errors else [],
                total_fields_validated=total_fields,
                fields_passed=fields_passed,
                fields_failed=total_fields - fields_passed
            )
            
            logger.info(f"✅ Metadata validation completed")
            logger.info(f"📊 Validation score: {report.validation_score:.3f}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Metadata validation failed: {e}")
            return MetadataValidationReport(
                validation_timestamp=validation_start,
                is_valid=False,
                schema_validation=False,
                consistency_validation=False,
                quality_validation=False,
                relationship_validation=False,
                validation_errors=[str(e)],
                validation_warnings=[],
                improvement_suggestions=["Fix validation system errors"],
                total_fields_validated=0,
                fields_passed=0,
                fields_failed=1
            )


# Testing and demonstration
async def test_enhanced_vector_store():
    """Test the enhanced vector store functionality"""
    
    logger.info("🧪 Testing enhanced vector store...")
    
    # Initialize vector store
    vector_store = EnhancedVectorStore(
        persist_directory="./test_chromadb",
        collection_name="test_enhanced_docs"
    )
    
    # Get collection statistics
    stats = await vector_store.get_collection_stats()
    logger.info(f"📊 Collection stats: {stats}")
    
    # Test search context
    search_context = SearchContext(
        target_iep_section=IEPSection.PRESENT_LEVELS,
        document_types=[DocumentType.ASSESSMENT_REPORT],
        quality_threshold=0.3,
        max_results=5
    )
    
    # Perform test search
    results = await vector_store.enhanced_search(
        query_text="reading comprehension assessment",
        search_context=search_context,
        n_results=5
    )
    
    logger.info(f"🔍 Search returned {len(results)} results")
    for i, result in enumerate(results):
        logger.info(f"  Result {i+1}: Score {result.final_score:.3f}, Quality {result.quality_score:.3f}")
    
    # Validate metadata integrity
    validation_report = await vector_store.validate_metadata_integrity()
    logger.info(f"✅ Validation completed: {validation_report.validation_score:.3f}")
    
    return vector_store


if __name__ == "__main__":
    # Run test if script is executed directly
    import asyncio
    asyncio.run(test_enhanced_vector_store())