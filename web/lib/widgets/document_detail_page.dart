import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:searchio/services/api_service.dart';
import 'package:url_launcher/url_launcher.dart';


class DocumentDetailPage extends StatefulWidget {
  final int docId;
  final String? title; 

  const DocumentDetailPage({
    Key? key,
    required this.docId,
    this.title,
  }) : super(key: key);

  @override
  State<DocumentDetailPage> createState() => _DocumentDetailPageState();
}

class _DocumentDetailPageState extends State<DocumentDetailPage>
    with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();

  late TabController _tabController;

  // Document data
  Map<String, dynamic>? _documentData;
  SearchResponse? _similarDocuments;

  // Loading states
  bool _isLoadingDocument = true;
  bool _isLoadingSimilar = true;

  // Error states
  String? _documentError;
  String? _similarError;

  // Settings for similar search
  int _numTerms = 20;
  int _topK = 10;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadDocumentData();
    _loadSimilarDocuments();
  }

  Future<void> _loadDocumentData() async {
    setState(() {
      _isLoadingDocument = true;
      _documentError = null;
    });

    try {
      final data = await _apiService.getDocument(widget.docId);
      setState(() {
        _documentData = data;
        _isLoadingDocument = false;
      });
    } catch (e) {
      setState(() {
        _documentError = e.toString();
        _isLoadingDocument = false;
      });
    }
  }

  Future<void> _loadSimilarDocuments() async {
    setState(() {
      _isLoadingSimilar = true;
      _similarError = null;
    });

    try {
      final response = await _apiService.findSimilar(
        docId: widget.docId,
        topK: _topK,
        numTerms: _numTerms,
      );
      setState(() {
        _similarDocuments = response;
        _isLoadingSimilar = false;
      });
    } catch (e) {
      setState(() {
        _similarError = e.toString();
        _isLoadingSimilar = false;
      });
    }
  }

  Future<void> _openUrl(String url) async {
    final uri = Uri.parse(Uri.encodeFull(url));
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Could not open URL: $url')),
        );
      }
    }
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Copied to clipboard!'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _navigateToDocument(int docId) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => DocumentDetailPage(docId: docId),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text(
          widget.title ?? _documentData?['title'] ?? 'Document ${widget.docId}',
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          // Open in Wikipedia button
          if (_documentData != null)
            IconButton(
              icon: const Icon(Icons.open_in_new),
              tooltip: 'Open in Wikipedia',
              onPressed: () => _openUrl(_documentData!['url']),
            ),
         
        ],
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(icon: Icon(Icons.description), text: 'Document'),
            Tab(icon: Icon(Icons.compare_arrows), text: 'Similar'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildDocumentTab(),
          _buildSimilarTab(),
        ],
      ),
    );
  }

  // ========== Document Details Tab ==========
  Widget _buildDocumentTab() {
    if (_isLoadingDocument) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_documentError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Error loading document',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(_documentError!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadDocumentData,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_documentData == null) {
      return const Center(child: Text('No data available'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Title Card
          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.article, color: Colors.blue),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _documentData!['title'],
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy),
                        tooltip: 'Copy title',
                        onPressed: () =>
                            _copyToClipboard(_documentData!['title']),
                      ),
                    ],
                  ),
                  const Divider(height: 24),
                  _buildInfoRow('Document ID', '${_documentData!['doc_id']}'),
                  _buildInfoRow('Length', '${_documentData!['length']} tokens'),
                  _buildInfoRow('URL', _documentData!['url'], isUrl: true),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Full Text Card
          Card(
            elevation: 2,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Full Text',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.copy),
                        tooltip: 'Copy text',
                        onPressed: () =>
                            _copyToClipboard(_documentData!['text']),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: SelectableText(
                      _documentData!['text'],
                      style: const TextStyle(
                        fontSize: 14,
                        height: 1.6,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isUrl = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
          ),
          Expanded(
            child: isUrl
                ? InkWell(
                    onTap: () => _openUrl(value),
                    child: Text(
                      value,
                      style: const TextStyle(
                        color: Colors.blue,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  )
                : SelectableText(value),
          ),
        ],
      ),
    );
  }

  // ========== Similar Documents Tab ==========
  Widget _buildSimilarTab() {
    return Column(
      children: [
        // Settings Card
        // Card(
        //   margin: const EdgeInsets.all(16),
        //   child: Padding(
        //     padding: const EdgeInsets.all(16),
        //     child: Column(
        //       crossAxisAlignment: CrossAxisAlignment.start,
        //       children: [
        //         Text(
        //           'Relevance Feedback Settings',
        //           style: Theme.of(context).textTheme.titleMedium?.copyWith(
        //                 fontWeight: FontWeight.bold,
        //               ),
        //         ),
        //         const SizedBox(height: 16),
        //         Row(
        //           children: [
        //             Expanded(
        //               child: Column(
        //                 crossAxisAlignment: CrossAxisAlignment.start,
        //                 children: [
        //                   Text('Number of Terms: $_numTerms'),
        //                   Slider(
        //                     value: _numTerms.toDouble(),
        //                     min: 5,
        //                     max: 50,
        //                     divisions: 9,
        //                     label: '$_numTerms',
        //                     onChanged: (value) {
        //                       setState(() {
        //                         _numTerms = value.toInt();
        //                       });
        //                     },
        //                   ),
        //                 ],
        //               ),
        //             ),
        //             const SizedBox(width: 16),
        //             Expanded(
        //               child: Column(
        //                 crossAxisAlignment: CrossAxisAlignment.start,
        //                 children: [
        //                   Text('Top K Results: $_topK'),
        //                   Slider(
        //                     value: _topK.toDouble(),
        //                     min: 5,
        //                     max: 20,
        //                     divisions: 3,
        //                     label: '$_topK',
        //                     onChanged: (value) {
        //                       setState(() {
        //                         _topK = value.toInt();
        //                       });
        //                     },
        //                   ),
        //                 ],
        //               ),
        //             ),
        //             ElevatedButton.icon(
        //               onPressed: _loadSimilarDocuments,
        //               icon: const Icon(Icons.search),
        //               label: const Text('Apply'),
        //             ),
        //           ],
        //         ),
        //       ],
        //     ),
        //   ),
        // ),

        // Results
        Expanded(
          child: _buildSimilarResults(),
        ),
      ],
    );
  }

  Widget _buildSimilarResults() {
    if (_isLoadingSimilar) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_similarError != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text('Error loading similar documents'),
            const SizedBox(height: 8),
            Text(_similarError!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loadSimilarDocuments,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
            ),
          ],
        ),
      );
    }

    if (_similarDocuments == null || _similarDocuments!.results.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('No similar documents found'),
          ],
        ),
      );
    }

    return Column(
      children: [
        // Results Header
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          color: Colors.blue[50],
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Found ${_similarDocuments!.totalResults} similar documents',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                'Search time: ${_similarDocuments!.searchTime.toStringAsFixed(4)}s',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),

        // Results List
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.all(8),
            itemCount: _similarDocuments!.results.length,
            itemBuilder: (context, index) {
              final result = _similarDocuments!.results[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                child: InkWell(
                  onTap: () => _navigateToDocument(result.docId),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Title and Score
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.blue[100],
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '#${index + 1}',
                                style: const TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                result.title,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: Colors.green[100],
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                "score ${result.score.toStringAsFixed(4)}",
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.green[700],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        // Snippet
                        Text(
                          result.textSnippet,
                          style: const TextStyle(
                            fontSize: 14,
                            color: Colors.black87,
                            height: 1.5,
                          ),
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 12),

                        // Actions
                        Row(
                          children: [
                            TextButton.icon(
                              onPressed: () =>
                                  _navigateToDocument(result.docId),
                              icon: const Icon(Icons.visibility, size: 18),
                              label: const Text('View Details'),
                            ),
                            TextButton.icon(
                              onPressed: () => _openUrl(result.url),
                              icon: const Icon(Icons.open_in_new, size: 18),
                              label: const Text('Open in Wiki'),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _tabController.dispose();
    _apiService.dispose();
    super.dispose();
  }
}
