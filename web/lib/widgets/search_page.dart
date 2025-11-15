import 'package:flutter/material.dart';

import 'package:searchio/constant/app_colors.dart';
import 'package:searchio/widgets/document_detail_page.dart';
import '../services/api_service.dart';

class SearchPage extends StatefulWidget {
  const SearchPage({Key? key}) : super(key: key);

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();

  SearchResponse? _searchResponse;
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkApiHealth();
  }

  Future<void> _checkApiHealth() async {
    try {
      final health = await _apiService.checkHealth();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('API Status: ${health['status']}'),
            backgroundColor:
                health['index_loaded'] ? Colors.green : Colors.orange,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to connect to API: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Future<void> _performSearch() async {
    if (_searchController.text.trim().isEmpty) {
      setState(() {
        _errorMessage = 'Please enter a search query';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.search(
        query: _searchController.text,
      
      );

      setState(() {
        _searchResponse = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _findSimilar(int docId) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _apiService.findSimilar(
        docId: docId,
        topK: 10,
      );

      setState(() {
        _searchResponse = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        title: Padding(
          padding: const EdgeInsets.all(10.0),
          child: RichText(
                text: const TextSpan(
                  style: TextStyle(
                    fontSize: 60,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Roboto',
                  ),
                  children: [
                    TextSpan(text: 'S', style: TextStyle(color: AppColors.googleBlue)),
                    TextSpan(text: 'E', style: TextStyle(color: AppColors.googleRed)),
                    TextSpan(text: 'A', style: TextStyle(color: AppColors.googleYellow)),
                    TextSpan(text: 'R', style: TextStyle(color: AppColors.googleBlue)),
                    TextSpan(text: 'C', style: TextStyle(color: AppColors.googleGreen)),
                    TextSpan(text: 'H', style: TextStyle(color: AppColors.googleRed)),
                    TextSpan(text: 'I', style: TextStyle(color: AppColors.googleYellow)),
                    TextSpan(text: 'O', style: TextStyle(color: AppColors.googleBlue)),
                  ],
                ),
              ),
        ),
      ),
      body: Column(
        children: [
          
          
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchController,
                    decoration: const InputDecoration(
                      hintText: 'Search Wikipedia...',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.search),
                    ),
                    onSubmitted: (_) => _performSearch(),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _isLoading ? null : _performSearch,
                  child: const Text('Search'),
                ),
              ],
            ),
          ),

         
          if (_errorMessage != null)
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Text(
                _errorMessage!,
                style: const TextStyle(color: Colors.red),
              ),
            ),

          // ⏳ Loading Indicator
          if (_isLoading)
            const Expanded(
              child: Center(child: CircularProgressIndicator()),
            ),

          // 📋 Search Results
          if (!_isLoading && _searchResponse != null)
            Expanded(
              child: Column(
                children: [
                  // Results Header
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Text(
                      'Found ${_searchResponse!.totalResults} results in ${_searchResponse!.searchTime}s',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),

                  // Results List
                  Expanded(
                    child: ListView.builder(
                      itemCount: _searchResponse!.results.length,
                      itemBuilder: (context, index) {
                        final result = _searchResponse!.results[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 8,
                          ),
                          child: ListTile(
                            title: Text(
                              result.title,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 8),
                                Text(result.textSnippet),
                                const SizedBox(height: 8),
                                Text(
                                  'Score: ${result.score.toStringAsFixed(4)}',
                                  style: const TextStyle(
                                    color: Colors.grey,
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                           
                            
                            onTap: () {
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => DocumentDetailPage(
                                    docId: result.docId,
                                    title: result.title,
                                  ),
                                ),
                              );
                            },
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    _apiService.dispose();
    super.dispose();
  }
}