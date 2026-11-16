import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../services/mock_data_service.dart';
import '../models/models.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isListeningVoice = false;

  final List<String> _quickPrompts = [
    'Ghi chi cà phê 35k',
    'Tạo task kiểm tra code AI4Life',
    'Trích 500k vào quỹ Laptop AI',
    'Xem tổng chi tiêu tháng này',
  ];

  void _sendMessage([String? customText]) {
    final text = customText ?? _controller.text.trim();
    if (text.isEmpty) return;

    final dataService = MockDataService();
    final userMsg = ChatMessage(
      id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
      text: text,
      isUser: true,
      time: DateTime.now(),
    );

    dataService.addChatMessage(userMsg);
    if (customText == null) _controller.clear();
    _scrollToBottom();

    // Simulate Dual-Path Router (Fast Path vs Reasoning Path vs HITL)
    Future.delayed(const Duration(milliseconds: 500), () {
      if (!mounted) return;
      _processBotResponse(text, dataService);
    });
  }

  void _processBotResponse(String text, MockDataService dataService) {
    final lower = text.toLowerCase();

    if (lower.contains('quỹ laptop') || (lower.contains('trích') && lower.contains('tiết kiệm'))) {
      // Human-in-the-Loop Workflow (ADR-0004)
      final hitlMsg = ChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
        text: 'OnisAgent đã nhận lệnh trích tiền. Theo chốt kiểm soát an toàn Human-in-the-Loop (ADR-0004), xin vui lòng xác nhận trước khi thực hiện:',
        isUser: false,
        time: DateTime.now(),
        fastPathTag: 'Reasoning Path • HITL Gate',
        hitlProposal: HitlActionProposal(
          id: 'hitl_${DateTime.now().millisecondsSinceEpoch}',
          actionType: 'transfer_savings',
          title: 'Trích ngân sách vào Quỹ Laptop AI',
          details: 'Chuyển 500.000 ₫ từ Số dư khả dụng sang quỹ "Đổi Laptop chạy Local AI Model".',
          amount: 500000,
          targetName: 'Đổi Laptop chạy Local AI Model (RTX GPU)',
          timestamp: DateTime.now(),
        ),
      );
      dataService.addChatMessage(hitlMsg);
    } else if (lower.contains('cà phê') || lower.contains('chi') || lower.contains('ăn') || lower.contains('mua')) {
      // Fast Path - Cash Flow Transaction (~5-12ms, 0 Token)
      double amount = 35000;
      if (lower.contains('35k') || lower.contains('35.000')) amount = 35000;
      if (lower.contains('45k') || lower.contains('45.000')) amount = 45000;

      dataService.addTransaction(
        TransactionItem(
          id: 'tx_${DateTime.now().millisecondsSinceEpoch}',
          description: text,
          amount: amount,
          type: 'expense',
          category: lower.contains('cà phê') || lower.contains('ăn') ? 'Ăn uống' : 'Mua sắm',
          date: DateTime.now(),
        ),
      );

      final reply = ChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
        text: 'Đã ghi nhận khoản chi: "$text" - ${NumberFormat.currency(locale: 'vi_VN', symbol: '₫', decimalDigits: 0).format(amount)} vào sổ quỹ. Số dư đã cập nhật tức thì với Python Decimal.',
        isUser: false,
        time: DateTime.now(),
        fastPathTag: 'Fast Path (~6ms) • 0 Token',
      );
      dataService.addChatMessage(reply);
    } else if (lower.contains('task') || lower.contains('việc') || lower.contains('kiểm tra')) {
      // Fast Path - Create Task
      dataService.addTask(
        TaskItem(
          id: 't_${DateTime.now().millisecondsSinceEpoch}',
          title: text,
          deadline: DateTime.now().add(const Duration(hours: 12)),
          priority: Priority.high,
          category: 'Kỹ thuật',
          isImportant: true,
        ),
      );

      final reply = ChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
        text: 'Đã thêm công việc: "$text" vào danh sách việc cần làm (Hạn chót đặt mặc định trong 12h tới).',
        isUser: false,
        time: DateTime.now(),
        fastPathTag: 'Fast Path (~8ms) • 0 Token',
      );
      dataService.addChatMessage(reply);
    } else {
      // Reasoning Path - Bedrock / Ollama
      final reply = ChatMessage(
        id: 'msg_${DateTime.now().millisecondsSinceEpoch}',
        text: 'Phân tích tổng thể OnisAgent: Bạn hiện có ${NumberFormat.currency(locale: 'vi_VN', symbol: '₫', decimalDigits: 0).format(dataService.balance)} số dư khả dụng, tỉ lệ chi tiêu tháng đạt ${(dataService.totalExpense / (dataService.totalIncome > 0 ? dataService.totalIncome : 1) * 100).toInt()}% ngân sách thu. Kế hoạch tài chính đang ở mức an toàn.',
        isUser: false,
        time: DateTime.now(),
        fastPathTag: 'Reasoning Path • Bedrock Swarm',
      );
      dataService.addChatMessage(reply);
    }

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

  void _openVoiceRecordingModal(BuildContext context) {
    setState(() => _isListeningVoice = true);

    showModalBottomSheet(
      context: context,
      isDismissible: true,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setSheetState) {
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 28),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withAlpha(40),
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.primaryLight, width: 2),
                  ),
                  child: const Icon(Icons.mic_rounded, color: AppColors.primaryLight, size: 36),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Onis Voice-First Đang Lắng Nghe...',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Ví dụ: "Ghi chi cà phê sữa 35k" hoặc "Tạo task nộp slide"',
                  style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13),
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(
                    12,
                    (i) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: 4,
                      height: (i % 3 == 0 ? 32 : (i % 2 == 0 ? 20 : 12)).toDouble(),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                FilledButton.tonal(
                  onPressed: () {
                    Navigator.pop(ctx);
                    setState(() => _isListeningVoice = false);
                    _sendMessage('Ghi chi cà phê 35k');
                  },
                  child: const Text('Mô phỏng: Nói "Ghi chi cà phê 35k"'),
                ),
              ],
            ),
          );
        },
      ),
    ).then((_) {
      if (mounted) setState(() => _isListeningVoice = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final dataService = MockDataService();

    return Column(
      children: [
        // Top Architecture Status Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          decoration: const BoxDecoration(
            color: AppColors.surfaceDark,
            border: Border(bottom: BorderSide(color: AppColors.borderDark)),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.bolt_rounded, color: AppColors.primaryLight, size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Kev Fast Path (~5-12ms)',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primaryLight),
                  ),
                ],
              ),
              Row(
                children: [
                  Icon(Icons.psychology_rounded, color: AppColors.info, size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Bedrock Grounded',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF94A3B8)),
                  ),
                ],
              ),
            ],
          ),
        ),

        // Quick Prompt Suggestions
        Container(
          height: 44,
          margin: const EdgeInsets.symmetric(vertical: 8),
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            scrollDirection: Axis.horizontal,
            itemCount: _quickPrompts.length,
            separatorBuilder: (context, index) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final prompt = _quickPrompts[index];
              return ActionChip(
                label: Text(prompt, style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1))),
                backgroundColor: AppColors.surfaceDark,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: AppColors.borderDark),
                ),
                onPressed: () => _sendMessage(prompt),
              );
            },
          ),
        ),

        // Messages List
        Expanded(
          child: ListenableBuilder(
            listenable: dataService,
            builder: (context, _) {
              return ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                itemCount: dataService.messages.length,
                itemBuilder: (context, index) {
                  final msg = dataService.messages[index];
                  return _buildMessageItem(msg, dataService);
                },
              );
            },
          ),
        ),

        // Bottom Input Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: const BoxDecoration(
            color: AppColors.surfaceDark,
            border: Border(top: BorderSide(color: AppColors.borderDark)),
          ),
          child: SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    textInputAction: TextInputAction.send,
                    onSubmitted: (_) => _sendMessage(),
                    decoration: InputDecoration(
                      hintText: 'Nhắn với Onis AI hoặc dùng lệnh thoại...',
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      suffixIcon: IconButton(
                        icon: const Icon(Icons.send_rounded, color: AppColors.primaryLight, size: 20),
                        onPressed: () => _sendMessage(),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                // Voice Mic Button
                Container(
                  decoration: BoxDecoration(
                    color: _isListeningVoice ? AppColors.expense : AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    icon: Icon(
                      _isListeningVoice ? Icons.mic_off_rounded : Icons.mic_rounded,
                      color: Colors.white,
                      size: 22,
                    ),
                    onPressed: () => _openVoiceRecordingModal(context),
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMessageItem(ChatMessage msg, MockDataService service) {
    final isUser = msg.isUser;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // Routing / System Tag Pill
          if (!isUser && msg.fastPathTag != null)
            Container(
              margin: const EdgeInsets.only(bottom: 6, left: 4),
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: const Color(0xFF334155),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                msg.fastPathTag!,
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.primaryLight),
              ),
            ),

          // Text Bubble
          Container(
            constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isUser ? AppColors.primary : AppColors.surfaceDark,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isUser ? 16 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 16),
              ),
              border: isUser ? null : Border.all(color: AppColors.borderDark),
            ),
            child: Text(
              msg.text,
              style: TextStyle(fontSize: 14, color: isUser ? Colors.white : const Color(0xFFF1F5F9), height: 1.4),
            ),
          ),

          // HITL Proposal Interactive Card
          if (msg.hitlProposal != null) ...[
            const SizedBox(height: 10),
            _buildHitlProposalCard(msg.hitlProposal!, service),
          ],

          // Timestamp
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 6, right: 6),
            child: Text(
              DateFormat('HH:mm').format(msg.time),
              style: const TextStyle(fontSize: 10, color: Color(0xFF64748B)),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHitlProposalCard(HitlActionProposal proposal, MockDataService service) {
    final isPending = proposal.status == HitlStatus.pending;
    final isApproved = proposal.status == HitlStatus.approved;

    return Container(
      constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isPending
              ? AppColors.warning
              : (isApproved ? AppColors.accent : const Color(0xFF64748B)),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isPending
                    ? Icons.gavel_rounded
                    : (isApproved ? Icons.check_circle_rounded : Icons.cancel_rounded),
                size: 18,
                color: isPending
                    ? AppColors.warning
                    : (isApproved ? AppColors.accent : const Color(0xFF94A3B8)),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  proposal.title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.white),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            proposal.details,
            style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1), height: 1.3),
          ),
          const SizedBox(height: 12),
          if (isPending)
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton(
                  style: OutlinedButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    side: const BorderSide(color: Color(0xFF64748B)),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  onPressed: () => service.rejectHitlProposal(proposal.id),
                  child: const Text('Hủy bỏ', style: TextStyle(color: Color(0xFF94A3B8), fontSize: 12)),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  style: FilledButton.styleFrom(
                    visualDensity: VisualDensity.compact,
                    backgroundColor: AppColors.accent,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  onPressed: () => service.approveHitlProposal(proposal.id),
                  child: const Text('Xác nhận thực hiện', style: TextStyle(fontSize: 12)),
                ),
              ],
            )
          else
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: (isApproved ? AppColors.accent : const Color(0xFF64748B)).withAlpha(25),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                isApproved ? '✅ Đã được phê duyệt & Thực thi' : '❌ Đã từ chối thực hiện',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: isApproved ? AppColors.accent : const Color(0xFF94A3B8),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
