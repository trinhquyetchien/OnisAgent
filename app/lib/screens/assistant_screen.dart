import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../services/mock_data_service.dart';
import '../models/models.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime time;
  final String? fastPathTag;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.time,
    this.fastPathTag,
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
  final List<ChatMessage> _messages = [
    ChatMessage(
      text: 'Chào bạn! Mình là trợ lý Onis AI. Bạn có thể ra lệnh ghi nhận thu/chi, tạo việc cần làm hoặc hỏi đáp tài chính.',
      isUser: false,
      time: DateTime.now().subtract(const Duration(minutes: 5)),
      fastPathTag: 'System 1 • Kev Model Ready',
    ),
  ];

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _messages.add(ChatMessage(text: text, isUser: true, time: DateTime.now()));
      _controller.clear();
    });

    // Mock Fast Path / LLM response
    Future.delayed(const Duration(milliseconds: 600), () {
      if (!mounted) return;
      _handleBotReply(text);
    });

    _scrollToBottom();
  }

  void _handleBotReply(String userText) {
    final lower = userText.toLowerCase();
    String reply;
    String tag = 'Fast Path (~8ms) • 0 Token';

    if (lower.contains('phở') || lower.contains('cà phê') || lower.contains('ăn')) {
      reply = 'Đã ghi nhận chi tiêu: "Ăn uống" - 45.000₫ vào sổ quỹ của bạn. Số dư đã được cập nhật chính xác với Python Decimal.';
      MockDataService().addTransaction(
        TransactionItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          description: userText,
          amount: 45000,
          type: 'expense',
          category: 'Ăn uống',
          date: DateTime.now(),
        ),
      );
    } else if (lower.contains('task') || lower.contains('việc') || lower.contains('nhắc')) {
      reply = 'Đã tạo công việc mới: "$userText". Hạn chót được đặt vào 18:00 hôm nay.';
      MockDataService().addTask(
        TaskItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          title: userText,
          deadline: DateTime.now().add(const Duration(hours: 6)),
          priority: Priority.high,
        ),
      );
    } else {
      tag = 'Reasoning Path • Bedrock / Ollama';
      reply = 'OnisAgent đã tiếp nhận câu hỏi của bạn. Đang suy luận và phân tích cơ cấu tài chính tổng thể...';
    }

    setState(() {
      _messages.add(ChatMessage(text: reply, isUser: false, time: DateTime.now(), fastPathTag: tag));
    });
    _scrollToBottom();
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
                  color: AppColors.accent.withAlpha(20),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  children: [
                    CircleAvatar(radius: 4, backgroundColor: AppColors.accent),
                    SizedBox(width: 6),
                    Text('Dual-Path Router Active', style: TextStyle(color: AppColors.accent, fontSize: 12)),
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
              return Align(
                alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
                child: Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  constraints: const BoxConstraints(maxWidth: 600),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: msg.isUser ? AppColors.primary : AppColors.surfaceDark,
                    borderRadius: BorderRadius.circular(16),
                    border: msg.isUser ? null : Border.all(color: const Color(0xFF334155)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (msg.fastPathTag != null) ...[
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.bolt_rounded, size: 14, color: AppColors.warning),
                            const SizedBox(width: 4),
                            Text(
                              msg.fastPathTag!,
                              style: const TextStyle(fontSize: 11, color: AppColors.warning, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                      ],
                      Text(msg.text, style: const TextStyle(fontSize: 15, height: 1.4)),
                    ],
                  ),
                ),
              );
            },
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
              Expanded(
                child: TextField(
                  controller: _controller,
                  decoration: InputDecoration(
                    hintText: 'Nhập câu lệnh (vd: vừa ăn phở 45k, tạo task hoàn thành báo cáo)...',
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
              IconButton.filled(
                onPressed: _sendMessage,
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
