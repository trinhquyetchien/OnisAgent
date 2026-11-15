import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/mock_data_service.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime time;
  final String? pathBadge;
  final String? intentTag;
  final double? confidence;
  final double? latencyMs;
  final List<String> quickReplies;
  final String? status;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.time,
    this.pathBadge,
    this.intentTag,
    this.confidence,
    this.latencyMs,
    this.quickReplies = const [],
    this.status,
  });
}

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late final ApiService _apiService;
  bool _isLoading = false;
  bool _isListening = false;

  final List<ChatMessage> _messages = [
    ChatMessage(
      text: 'Chào bạn! Mình là trợ lý Onis AI. Bạn có thể ra lệnh ghi nhận thu/chi, tạo việc cần làm hoặc hỏi đáp tài chính.',
      isUser: false,
      time: DateTime.now().subtract(const Duration(minutes: 5)),
      pathBadge: 'Fast Path (~6ms)',
      intentTag: 'system.greeting',
      confidence: 0.99,
      latencyMs: 6.2,
      quickReplies: ['Vừa ăn phở 45k', 'Tạo task làm báo cáo AI4Life', 'Số dư hiện tại'],
    ),
  ];

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
  }

  void _sendMessage([String? overrideText]) async {
    final text = (overrideText ?? _controller.text).trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(
        text: text,
        isUser: true,
        time: DateTime.now(),
      ));
      if (overrideText == null) {
        _controller.clear();
      }
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await _apiService.sendMessage(text: text);

      if (!mounted) return;

      // Update local dashboard mock stores if transaction or task is ready
      if (response.status == 'READY') {
        _syncLocalDashboard(response, text);
      }

      setState(() {
        _isLoading = false;
        _messages.add(ChatMessage(
          text: response.reply,
          isUser: false,
          time: DateTime.now(),
          pathBadge: response.path,
          intentTag: response.intent,
          confidence: response.confidence,
          latencyMs: response.latencyMs,
          quickReplies: response.quickReplies,
          status: response.status,
        ));
      });
    } catch (e) {
      if (!mounted) return;
      // Fallback offline handler
      _handleOfflineFallback(text);
    }

    _scrollToBottom();
  }

  void _syncLocalDashboard(ChatApiResponse response, String originalText) {
    if (response.intent.startsWith('finance.add_expense')) {
      final amount = double.tryParse(response.slots['amount']?.toString() ?? '45000') ?? 45000;
      MockDataService().addTransaction(
        TransactionItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          description: response.slots['note']?.toString() ?? originalText,
          amount: amount,
          type: 'expense',
          category: response.slots['category']?.toString() ?? 'Ăn uống',
          date: DateTime.now(),
        ),
      );
    } else if (response.intent.startsWith('task.create')) {
      MockDataService().addTask(
        TaskItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          title: response.slots['title']?.toString() ?? originalText,
          deadline: DateTime.now().add(const Duration(hours: 6)),
          priority: Priority.high,
        ),
      );
    }
  }

  void _handleOfflineFallback(String text) {
    final lower = text.toLowerCase();
    String reply;
    String badge = 'Fast Path (~8ms) • Offline Fallback';
    String intent = 'finance.add_expense';
    double confidence = 0.88;
    List<String> replies = [];

    if (lower.contains('phở') || lower.contains('cà phê') || lower.contains('ăn')) {
      reply = 'Đã ghi nhận chi tiêu: 45.000₫ vào sổ quỹ. (Kết nối Backend Offline fallback)';
      MockDataService().addTransaction(
        TransactionItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          description: text,
          amount: 45000,
          type: 'expense',
          category: 'Ăn uống',
          date: DateTime.now(),
        ),
      );
    } else if (lower.contains('task') || lower.contains('việc') || lower.contains('nhắc')) {
      intent = 'task.create';
      reply = 'Đã tạo công việc mới: "$text". Hạn chót được đặt vào 18:00 hôm nay.';
      MockDataService().addTask(
        TaskItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          title: text,
          deadline: DateTime.now().add(const Duration(hours: 6)),
          priority: Priority.high,
        ),
      );
    } else if (lower.contains('mua đồ')) {
      intent = 'finance.add_expense';
      reply = "Bạn đã chi bao nhiêu tiền cho khoản mua sắm này vậy?";
      replies = ['30.000₫', '50.000₫', '100.000₫', '200.000₫'];
    } else {
      badge = 'Reasoning Path • Bedrock Swarm';
      intent = 'finance.financial_report';
      confidence = 0.55;
      reply = 'OnisAgent đã tiếp nhận câu hỏi của bạn. Đang suy luận và phân tích cơ cấu tài chính tổng thể...';
    }

    setState(() {
      _isLoading = false;
      _messages.add(ChatMessage(
        text: reply,
        isUser: false,
        time: DateTime.now(),
        pathBadge: badge,
        intentTag: intent,
        confidence: confidence,
        latencyMs: 7.8,
        quickReplies: replies,
      ));
    });
    _scrollToBottom();
  }

  void _simulateVoiceTest() {
    setState(() {
      _isListening = true;
    });

    // Simulate Voice Push-to-Talk speech recognition
    Future.delayed(const Duration(milliseconds: 1200), () {
      if (!mounted) return;
      setState(() {
        _isListening = false;
        _controller.text = 'vừa ăn phở 45k';
      });
      _sendMessage();
    });
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Top Info Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          decoration: const BoxDecoration(
            color: AppColors.surfaceDark,
            border: Border(bottom: BorderSide(color: Color(0xFF334155))),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.smart_toy_rounded, color: AppColors.primaryLight, size: 22),
                  SizedBox(width: 10),
                  Text('Onis AI Cognitive Agent', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.accent.withAlpha(25),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.accent.withAlpha(80)),
                ),
                child: const Row(
                  children: [
                    CircleAvatar(radius: 4, backgroundColor: AppColors.accent),
                    SizedBox(width: 6),
                    Text('Fast Path & Kev Model Online', style: TextStyle(color: AppColors.accent, fontSize: 12, fontWeight: FontWeight.w500)),
                  ],
                ),
              ),
            ],
          ),
        ),

        // Message List
        Expanded(
          child: ListView.builder(
            controller: _scrollController,
            padding: const EdgeInsets.all(24),
            itemCount: _messages.length,
            itemBuilder: (context, index) {
              final msg = _messages[index];
              final isFastPath = msg.pathBadge?.contains('Fast Path') ?? true;

              return Align(
                alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  constraints: const BoxConstraints(maxWidth: 650),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: msg.isUser ? AppColors.primary : AppColors.surfaceDark,
                    borderRadius: BorderRadius.circular(16),
                    border: msg.isUser ? null : Border.all(color: const Color(0xFF334155)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Badge info on AI message
                      if (!msg.isUser && (msg.pathBadge != null || msg.intentTag != null)) ...[
                        Wrap(
                          spacing: 6,
                          runSpacing: 4,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            // Latency & Path Badge
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: isFastPath ? const Color(0xFF10B981).withAlpha(30) : Colors.purple.withAlpha(30),
                                borderRadius: BorderRadius.circular(12),
                                border: Border.all(
                                  color: isFastPath ? const Color(0xFF10B981) : Colors.purpleAccent,
                                  width: 0.8,
                                ),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    isFastPath ? Icons.bolt_rounded : Icons.psychology_rounded,
                                    size: 13,
                                    color: isFastPath ? const Color(0xFF10B981) : Colors.purpleAccent,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    msg.latencyMs != null
                                        ? '${msg.pathBadge} (${msg.latencyMs!.toStringAsFixed(1)}ms)'
                                        : (msg.pathBadge ?? 'Fast Path'),
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: isFastPath ? const Color(0xFF10B981) : Colors.purpleAccent,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),

                            // Intent Tag & Confidence Badge
                            if (msg.intentTag != null)
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: const Color(0xFF1E293B),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: const Color(0xFF475569), width: 0.8),
                                ),
                                child: Text(
                                  msg.confidence != null
                                      ? '${msg.intentTag} • ${(msg.confidence! * 100).toStringAsFixed(0)}%'
                                      : msg.intentTag!,
                                  style: const TextStyle(fontSize: 11, color: Color(0xFF94A3B8), fontWeight: FontWeight.w500),
                                ),
                              ),

                            // Clarification Status indicator
                            if (msg.status == 'NEED_CLARIFICATION')
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                decoration: BoxDecoration(
                                  color: AppColors.warning.withAlpha(30),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppColors.warning, width: 0.8),
                                ),
                                child: const Text(
                                  'Cần làm rõ',
                                  style: TextStyle(fontSize: 11, color: AppColors.warning, fontWeight: FontWeight.bold),
                                ),
                              ),
                          ],
                        ),
                        const SizedBox(height: 8),
                      ],

                      // Message Body
                      Text(
                        msg.text,
                        style: const TextStyle(fontSize: 15, height: 1.45, color: Colors.white),
                      ),

                      // Quick-reply Action Chips
                      if (!msg.isUser && msg.quickReplies.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        const Text(
                          'Gợi ý chọn nhanh:',
                          style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8), fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 6),
                        Wrap(
                          spacing: 8,
                          runSpacing: 6,
                          children: msg.quickReplies.map((replyText) {
                            return ActionChip(
                              avatar: const Icon(Icons.touch_app_rounded, size: 14, color: AppColors.primaryLight),
                              label: Text(
                                replyText,
                                style: const TextStyle(fontSize: 13, color: Colors.white, fontWeight: FontWeight.w500),
                              ),
                              backgroundColor: const Color(0xFF1E293B),
                              side: const BorderSide(color: Color(0xFF3B82F6), width: 0.8),
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                              onPressed: () => _sendMessage(replyText),
                            );
                          }).toList(),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            },
          ),
        ),

        // Loading indicator
        if (_isLoading)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent),
                ),
                const SizedBox(width: 8),
                Text(
                  'Kev Fast Path đang phản xạ (~6ms)...',
                  style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                ),
              ],
            ),
          ),

        // Chat Input Bar
        Container(
          padding: const EdgeInsets.all(16),
          decoration: const BoxDecoration(
            color: AppColors.surfaceDark,
            border: Border(top: BorderSide(color: Color(0xFF334155))),
          ),
          child: Row(
            children: [
              // Voice PTT Test Button
              IconButton(
                onPressed: _simulateVoiceTest,
                tooltip: 'Nhấn nói tiếng Việt (Voice PTT Test)',
                icon: Icon(
                  _isListening ? Icons.mic_rounded : Icons.mic_none_rounded,
                  color: _isListening ? Colors.redAccent : AppColors.accent,
                ),
                style: IconButton.styleFrom(
                  backgroundColor: _isListening ? Colors.redAccent.withAlpha(30) : AppColors.backgroundDark,
                  padding: const EdgeInsets.all(12),
                ),
              ),
              const SizedBox(width: 8),

              // Text Field
              Expanded(
                child: TextField(
                  controller: _controller,
                  style: const TextStyle(color: Colors.white),
                  decoration: InputDecoration(
                    hintText: 'Nhập câu lệnh (vd: vừa ăn phở 45k, tạo task slide AI4Life)...',
                    hintStyle: TextStyle(color: Colors.grey[500], fontSize: 14),
                    filled: true,
                    fillColor: AppColors.backgroundDark,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: const BorderSide(color: Color(0xFF334155)),
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                  onSubmitted: (_) => _sendMessage(),
                ),
              ),
              const SizedBox(width: 12),

              // Send Button
              IconButton.filled(
                onPressed: () => _sendMessage(),
                icon: const Icon(Icons.send_rounded),
                style: IconButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.all(14),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
