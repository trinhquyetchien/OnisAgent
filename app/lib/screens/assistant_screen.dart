import 'dart:async';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../theme/app_theme.dart';
import '../services/app_data_service.dart';
import '../services/api_service.dart';
import '../services/auth/auth_state_notifier.dart';
import '../models/models.dart';

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen>
    with AutomaticKeepAliveClientMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  late final ApiService _apiService;
  bool _isLoading = false;
  bool _isListeningVoice = false;

  @override
  bool get wantKeepAlive => true;

  final List<String> _quickPrompts = [
    'Ghi chi cà phê 35k',
    'Tạo task kiểm tra code AI4Life',
    'Trích 500k vào quỹ Laptop AI',
    'Xem tổng chi tiêu tháng này',
  ];

  @override
  void initState() {
    super.initState();
    _apiService = ApiService();
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage([String? overrideText]) async {
    final text = (overrideText ?? _controller.text).trim();
    if (text.isEmpty) return;

    final dataService = AppDataService();
    final userMsg = ChatMessage(text: text, isUser: true, time: DateTime.now());

    dataService.addChatMessage(userMsg);
    if (overrideText == null) {
      _controller.clear();
    }
    setState(() {
      _isLoading = true;
    });
    _scrollToBottom();

    final idempotencyKey = 'chat_${DateTime.now().microsecondsSinceEpoch}';
    try {
      final response = await _apiService.sendMessage(
        text: text,
        userId: AuthStateNotifier().currentUser?.id,
        idempotencyKey: idempotencyKey,
      );
      if (!mounted) return;

      if (response.status == 'READY') {
        await _syncLocalDashboard(dataService);
      } else if (response.requiresHitl) {
        final action = switch (response.intent) {
          final intent when intent.startsWith('task.delete') => 'task_delete',
          final intent when intent.startsWith('finance.transfer') => 'transfer',
          final intent when intent.startsWith('finance.savings_goal') =>
            'savings_create',
          final intent
              when intent.startsWith('finance.loan_installment_plan') ||
                  intent.startsWith('finance.loan.calculate') =>
            'loan_apply',
          _ => 'chat_confirm',
        };
        final directAction = action != 'chat_confirm';
        final payload = Map<String, dynamic>.from(response.slots);
        if (action == 'task_delete' &&
            payload['task_id'] == null &&
            payload['title'] == null &&
            payload['task_name'] != null) {
          payload['title'] = payload['task_name'];
        }
        dataService.addChatHitlProposal(
          action: action,
          payload: directAction
              ? payload
              : {'text': text, 'slots': response.slots},
          title: 'Xác nhận thao tác',
          details: response.reply,
          idempotencyKey:
              response.data['idempotency_key']?.toString() ?? idempotencyKey,
        );
      }

      final botMsg = ChatMessage(
        text: response.reply,
        isUser: false,
        time: DateTime.now(),
        pathBadge: response.path,
        fastPathTag: response.path,
        intentTag: response.intent,
        confidence: response.confidence,
        latencyMs: response.latencyMs,
        quickReplies: response.quickReplies,
        status: response.status,
      );
      dataService.addChatMessage(botMsg);
    } on Exception catch (e) {
      if (!mounted) return;
      _handleOfflineFallback(text, dataService, e);
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
        _scrollToBottom();
      }
    }
  }

  Future<void> _syncLocalDashboard(AppDataService dataService) async {
    await dataService.refresh();
  }

  Future<void> _approveProposal(
    HitlActionProposal proposal,
    AppDataService service,
  ) async {
    if (proposal.actionType != 'chat_confirm') {
      await service.approveHitlProposal(proposal.id);
      return;
    }

    try {
      final slots = proposal.payload['slots'];
      final response = await _apiService.sendMessage(
        text: proposal.payload['text']?.toString() ?? '',
        slots: slots is Map<String, dynamic> ? slots : null,
        userConfirmed: true,
        idempotencyKey: proposal.idempotencyKey,
        userId: AuthStateNotifier().currentUser?.id,
      );
      if (response.status == 'READY') {
        service.markHitlProposalStatus(proposal.id, HitlStatus.approved);
        await service.refresh();
      }
      service.addChatMessage(
        ChatMessage(
          text: response.reply,
          isUser: false,
          time: DateTime.now(),
          pathBadge: response.path,
          intentTag: response.intent,
          confidence: response.confidence,
          latencyMs: response.latencyMs,
          quickReplies: response.quickReplies,
          status: response.status,
        ),
      );
    } on Exception catch (error) {
      service.addChatMessage(
        ChatMessage(
          text: 'Không thể xác nhận thao tác với backend: $error',
          isUser: false,
          time: DateTime.now(),
          pathBadge: 'API error',
          status: 'FAILED',
        ),
      );
    }
  }

  void _handleOfflineFallback(
    String text,
    AppDataService dataService,
    Exception error,
  ) {
    dataService.addChatMessage(
      ChatMessage(
        text: 'Không thể gửi yêu cầu tới backend cho "$text": $error',
        isUser: false,
        time: DateTime.now(),
        pathBadge: 'API error',
        status: 'FAILED',
      ),
    );
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
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

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
                    color: AppColors.primary.withAlpha(isDark ? 40 : 25),
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.primary, width: 2),
                  ),
                  child: const Icon(
                    Icons.mic_rounded,
                    color: AppColors.primary,
                    size: 36,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  'Onis Voice-First Đang Lắng Nghe...',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: theme.colorScheme.onSurface,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Ví dụ: "Ghi chi cà phê sữa 35k" hoặc "Tạo task nộp slide"',
                  style: TextStyle(
                    color: isDark
                        ? const Color(0xFF94A3B8)
                        : const Color(0xFF64748B),
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 24),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: List.generate(
                    12,
                    (i) => Container(
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: 4,
                      height: (i % 3 == 0 ? 32 : (i % 2 == 0 ? 20 : 12))
                          .toDouble(),
                      decoration: BoxDecoration(
                        color: AppColors.primary,
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
    super.build(context);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final dataService = AppDataService();

    return Column(
      children: [
        // Top Architecture Status Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            border: Border(
              bottom: BorderSide(color: theme.colorScheme.outline),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Row(
                children: [
                  Icon(Icons.bolt_rounded, color: AppColors.primary, size: 16),
                  SizedBox(width: 6),
                  Text(
                    'Kev Fast Path (~5-12ms)',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  const Icon(
                    Icons.psychology_rounded,
                    color: AppColors.info,
                    size: 16,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    'Ollama Grounded',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                      color: isDark
                          ? const Color(0xFF94A3B8)
                          : const Color(0xFF64748B),
                    ),
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
                label: Text(
                  prompt,
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark
                        ? const Color(0xFFCBD5E1)
                        : const Color(0xFF334155),
                  ),
                ),
                backgroundColor: isDark
                    ? AppColors.surfaceDark
                    : const Color(0xFFF1F5F9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: BorderSide(color: theme.colorScheme.outline),
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
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                itemCount: dataService.messages.length,
                itemBuilder: (context, index) {
                  final msg = dataService.messages[index];
                  return _buildMessageItem(context, msg, dataService);
                },
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
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  'Kev Fast Path đang phản xạ (~6ms)...',
                  style: TextStyle(
                    fontSize: 12,
                    color: isDark ? Colors.grey[400] : Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),

        // Bottom Input Bar
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            border: Border(top: BorderSide(color: theme.colorScheme.outline)),
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
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 12,
                      ),
                      suffixIcon: IconButton(
                        icon: const Icon(
                          Icons.send_rounded,
                          color: AppColors.primary,
                          size: 20,
                        ),
                        onPressed: () => _sendMessage(),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                // Voice Mic Button
                Container(
                  decoration: BoxDecoration(
                    color: _isListeningVoice
                        ? AppColors.expense
                        : AppColors.primary,
                    shape: BoxShape.circle,
                  ),
                  child: IconButton(
                    icon: Icon(
                      _isListeningVoice
                          ? Icons.mic_off_rounded
                          : Icons.mic_rounded,
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

  Widget _buildMessageItem(
    BuildContext context,
    ChatMessage msg,
    AppDataService service,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isUser = msg.isUser;
    final badgeText = msg.effectivePathBadge;
    final isFastPath = badgeText?.contains('Fast Path') ?? true;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: isUser
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start,
        children: [
          // Routing / System Tag Pill
          if (!isUser && (badgeText != null || msg.intentTag != null)) ...[
            Wrap(
              spacing: 6,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                if (badgeText != null)
                  Container(
                    margin: const EdgeInsets.only(bottom: 4, left: 2),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: isFastPath
                          ? (isDark
                                ? const Color(0xFF10B981).withAlpha(35)
                                : const Color(0xFFD1FAE5))
                          : (isDark
                                ? const Color(0xFF8B5CF6).withAlpha(35)
                                : const Color(0xFFEDE9FE)),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isFastPath
                            ? const Color(0xFF10B981)
                            : const Color(0xFF8B5CF6),
                        width: 0.8,
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isFastPath
                              ? Icons.bolt_rounded
                              : Icons.psychology_rounded,
                          size: 13,
                          color: isFastPath
                              ? const Color(0xFF10B981)
                              : const Color(0xFF8B5CF6),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          msg.latencyMs != null
                              ? '$badgeText (${msg.latencyMs!.toStringAsFixed(1)}ms)'
                              : badgeText,
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isFastPath
                                ? (isDark
                                      ? const Color(0xFF34D399)
                                      : const Color(0xFF065F46))
                                : (isDark
                                      ? const Color(0xFFA78BFA)
                                      : const Color(0xFF5B21B6)),
                          ),
                        ),
                      ],
                    ),
                  ),

                if (msg.intentTag != null)
                  Container(
                    margin: const EdgeInsets.only(bottom: 4),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: isDark
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: theme.colorScheme.outline,
                        width: 0.8,
                      ),
                    ),
                    child: Text(
                      msg.confidence != null
                          ? '${msg.intentTag} • ${(msg.confidence! * 100).toStringAsFixed(0)}%'
                          : msg.intentTag!,
                      style: TextStyle(
                        fontSize: 10,
                        color: isDark
                            ? const Color(0xFF94A3B8)
                            : const Color(0xFF475569),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),

                if (msg.status == 'NEED_CLARIFICATION')
                  Container(
                    margin: const EdgeInsets.only(bottom: 4),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.warning.withAlpha(isDark ? 40 : 25),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.warning, width: 0.8),
                    ),
                    child: const Text(
                      'Cần làm rõ',
                      style: TextStyle(
                        fontSize: 10,
                        color: AppColors.warning,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
              ],
            ),
          ],

          // Text Bubble
          Container(
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.8,
            ),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: isUser
                  ? AppColors.primary
                  : (isDark ? AppColors.surfaceDark : const Color(0xFFF1F5F9)),
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(16),
                topRight: const Radius.circular(16),
                bottomLeft: Radius.circular(isUser ? 16 : 4),
                bottomRight: Radius.circular(isUser ? 4 : 16),
              ),
              border: isUser
                  ? null
                  : Border.all(color: theme.colorScheme.outline),
            ),
            child: Text(
              msg.text,
              style: TextStyle(
                fontSize: 14,
                color: isUser
                    ? Colors.white
                    : (isDark
                          ? const Color(0xFFF1F5F9)
                          : const Color(0xFF0F172A)),
                height: 1.4,
              ),
            ),
          ),

          // Quick Replies
          if (!isUser && msg.quickReplies.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: msg.quickReplies.map((replyText) {
                return ActionChip(
                  avatar: const Icon(
                    Icons.touch_app_rounded,
                    size: 13,
                    color: AppColors.primary,
                  ),
                  label: Text(
                    replyText,
                    style: TextStyle(
                      fontSize: 12,
                      color: isDark
                          ? const Color(0xFFCBD5E1)
                          : const Color(0xFF334155),
                    ),
                  ),
                  backgroundColor: isDark
                      ? const Color(0xFF1E293B)
                      : const Color(0xFFEEF2FF),
                  side: BorderSide(
                    color: isDark
                        ? const Color(0xFF3B82F6)
                        : const Color(0xFF818CF8),
                    width: 0.8,
                  ),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                  onPressed: () => _sendMessage(replyText),
                );
              }).toList(),
            ),
          ],

          // HITL Proposal Interactive Card
          if (msg.hitlProposal != null) ...[
            const SizedBox(height: 10),
            _buildHitlProposalCard(context, msg.hitlProposal!, service),
          ],

          // Timestamp
          Padding(
            padding: const EdgeInsets.only(top: 4, left: 6, right: 6),
            child: Text(
              DateFormat('HH:mm').format(msg.time),
              style: TextStyle(
                fontSize: 10,
                color: isDark
                    ? const Color(0xFF64748B)
                    : const Color(0xFF94A3B8),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHitlProposalCard(
    BuildContext context,
    HitlActionProposal proposal,
    AppDataService service,
  ) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isPending = proposal.status == HitlStatus.pending;
    final isApproved = proposal.status == HitlStatus.approved;

    return Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.of(context).size.width * 0.85,
      ),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E293B) : const Color(0xFFFFFBEB),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isPending
              ? AppColors.warning
              : (isApproved
                    ? AppColors.accent
                    : (isDark
                          ? const Color(0xFF64748B)
                          : const Color(0xFFCBD5E1))),
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
                    : (isApproved
                          ? Icons.check_circle_rounded
                          : Icons.cancel_rounded),
                size: 18,
                color: isPending
                    ? AppColors.warning
                    : (isApproved ? AppColors.accent : AppColors.expense),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  proposal.title,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: isPending
                      ? AppColors.warning.withAlpha(isDark ? 40 : 25)
                      : (isApproved
                            ? AppColors.accent.withAlpha(isDark ? 40 : 25)
                            : AppColors.expense.withAlpha(isDark ? 40 : 25)),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  isPending
                      ? 'Chờ duyệt'
                      : (isApproved ? 'Đã duyệt' : 'Từ chối'),
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: isPending
                        ? AppColors.warning
                        : (isApproved ? AppColors.accent : AppColors.expense),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            proposal.details,
            style: TextStyle(
              fontSize: 12,
              color: isDark ? const Color(0xFFCBD5E1) : const Color(0xFF475569),
            ),
          ),
          if (proposal.amount != null) ...[
            const SizedBox(height: 8),
            Text(
              NumberFormat.currency(
                locale: 'vi_VN',
                symbol: '₫',
                decimalDigits: 0,
              ).format(proposal.amount),
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppColors.warning,
              ),
            ),
          ],
          if (isPending) ...[
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                OutlinedButton(
                  onPressed: () => service.rejectHitlProposal(proposal.id),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: AppColors.expense,
                    side: const BorderSide(color: AppColors.expense),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 6,
                    ),
                    visualDensity: VisualDensity.compact,
                  ),
                  child: const Text('Từ chối'),
                ),
                const SizedBox(width: 8),
                FilledButton(
                  onPressed: () => _approveProposal(proposal, service),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 6,
                    ),
                    visualDensity: VisualDensity.compact,
                  ),
                  child: const Text('Phê duyệt'),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
