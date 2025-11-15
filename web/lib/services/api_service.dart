import 'dart:convert';
import 'package:http/http.dart' as http;

class SearchResult {
  final int docId;
  final String title;
  final String textSnippet;
  final double score;
  final String url;

  SearchResult({
    required this.docId,
    required this.title,
    required this.textSnippet,
    required this.score,
    required this.url,
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      docId: json['doc_id'],
      title: json['title'],
      textSnippet: json['text_snippet'],
      score: (json['score'] as num).toDouble(),
      url: json['url'],
    );
  }
}

class SearchResponse {
  final String query;
  final int totalResults;
  final List<SearchResult> results;
  final double searchTime;

  SearchResponse({
    required this.query,
    required this.totalResults,
    required this.results,
    required this.searchTime,
  });

  factory SearchResponse.fromJson(Map<String, dynamic> json) {
    return SearchResponse(
      query: json['query'],
      totalResults: json['total_results'],
      results: (json['results'] as List)
          .map((item) => SearchResult.fromJson(item))
          .toList(),
      searchTime: (json['search_time'] as num).toDouble(),
    );
  }
}

class ApiService {
 
  static const String baseUrl = 'http://localhost:8000';
  
 
  // static const String baseUrl = 'http://127.0.0.1:8000';
  
  
  // static const String baseUrl = 'http://192.168.1.X:8000';

  final http.Client _client = http.Client();

  // Health Check
  Future<Map<String, dynamic>> checkHealth() async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/health'),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Health check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to connect to API: $e');
    }
  }

  // Get Index Statistics
  Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/health/stats'),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get stats: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get stats: $e');
    }
  }

  // Search Documents
  Future<SearchResponse> search({
    required String query,
    
  }) async {
    try {
      final uri = Uri.parse(baseUrl).replace(
    path: '/search',
    queryParameters: {
      'search_query': query, 
    },
  );
      final response = await _client.get(
       uri,
        headers: {'Content-Type': 'application/json'},
        
    
      );

      if (response.statusCode == 200) {
        return SearchResponse.fromJson(json.decode(response.body));
      } else if (response.statusCode == 400) {
        throw Exception('Invalid query: ${response.body}');
      } else if (response.statusCode == 503) {
        throw Exception('Search engine not initialized');
      } else {
        throw Exception('Search failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Search error: $e');
    }
  }

  // Find Similar Documents (Relevance Feedback)
  Future<SearchResponse> findSimilar({
    required int docId,
    int topK = 10,
    int numTerms = 20,
    double k1 = 1.2,
    double b = 0.75,
  }) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/search/similar'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'doc_id': docId,
          'top_k': topK,
          'num_terms': numTerms,
          'k1': k1,
          'b': b,
        }),
      );

      if (response.statusCode == 200) {
        return SearchResponse.fromJson(json.decode(response.body));
      } else if (response.statusCode == 404) {
        throw Exception('Document not found');
      } else if (response.statusCode == 503) {
        throw Exception('Search engine not initialized');
      } else {
        throw Exception('Similar search failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Similar search error: $e');
    }
  }

  // Get Full Document
  Future<Map<String, dynamic>> getDocument(int docId) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/search/document/$docId'),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else if (response.statusCode == 404) {
        throw Exception('Document not found');
      } else {
        throw Exception('Failed to get document: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Get document error: $e');
    }
  }

  void dispose() {
    _client.close();
  }
}

