import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../../services/api_client.dart';
import '../../utils/constants.dart';

class DiseaseDetectionScreen extends StatefulWidget {
  const DiseaseDetectionScreen({super.key});

  @override
  State<DiseaseDetectionScreen> createState() => _DiseaseDetectionScreenState();
}

class _DiseaseDetectionScreenState extends State<DiseaseDetectionScreen> {
  File? _selectedImage;
  Map<String, dynamic>? _analysisResult;
  bool _isAnalyzing = false;
  final ImagePicker _picker = ImagePicker();

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? image = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (image != null) {
        setState(() {
          _selectedImage = File(image.path);
          _analysisResult = null;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('خطأ في اختيار الصورة: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  Future<void> _analyzeImage() async {
    if (_selectedImage == null) return;

    setState(() {
      _isAnalyzing = true;
    });

    try {
      // قراءة الصورة وتحويلها إلى base64
      final bytes = await _selectedImage!.readAsBytes();
      final base64Image = base64Encode(bytes);

      // إرسال إلى API
      final apiClient = context.read<ApiClient>();
      final response = await apiClient.post(
        '/ai/detect-disease/',
        data: {
          'image': base64Image,
          'save_image': false,
        },
      );

      setState(() {
        _analysisResult = response.data;
        _isAnalyzing = false;
      });
    } catch (e) {
      setState(() {
        _isAnalyzing = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('فشل التحليل: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('كشف أمراض النباتات'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // معلومات توضيحية
            Card(
              color: AppColors.info.withOpacity(0.1),
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: AppColors.info),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        'التقط صورة واضحة لورقة النبات للحصول على تشخيص دقيق',
                        style: AppTextStyles.body2.copyWith(color: AppColors.info),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),

            // عرض الصورة
            if (_selectedImage != null)
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppBorderRadius.md),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppBorderRadius.md),
                  child: Image.file(
                    _selectedImage!,
                    height: 300,
                    width: double.infinity,
                    fit: BoxFit.cover,
                  ),
                ),
              )
            else
              Container(
                height: 300,
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(AppBorderRadius.md),
                  border: Border.all(color: Colors.grey[400]!, width: 2, style: BorderStyle.solid),
                ),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.image_outlined, size: 80, color: Colors.grey[400]),
                      const SizedBox(height: AppSpacing.md),
                      Text(
                        'لم يتم اختيار صورة',
                        style: AppTextStyles.body1.copyWith(color: Colors.grey[600]),
                      ),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: AppSpacing.lg),

            // أزرار الإجراءات
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.camera),
                    icon: const Icon(Icons.camera_alt),
                    label: const Text('التقاط صورة'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                    ),
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _pickImage(ImageSource.gallery),
                    icon: const Icon(Icons.photo_library),
                    label: const Text('من المعرض'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),

            // زر التحليل
            ElevatedButton.icon(
              onPressed: _selectedImage != null && !_isAnalyzing ? _analyzeImage : null,
              icon: _isAnalyzing
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 2,
                      ),
                    )
                  : const Icon(Icons.analytics),
              label: Text(_isAnalyzing ? 'جاري التحليل...' : 'تحليل الصورة'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
              ),
            ),

            // عرض النتائج
            if (_analysisResult != null) ...[
              const SizedBox(height: AppSpacing.xl),
              _buildAnalysisResults(),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysisResults() {
    final isHealthy = _analysisResult!['is_healthy'] ?? false;
    final confidence = (_analysisResult!['confidence'] * 100).toStringAsFixed(1);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // حالة النبات
        Card(
          color: isHealthy ? AppColors.success.withOpacity(0.1) : AppColors.warning.withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: Column(
              children: [
                Icon(
                  isHealthy ? Icons.check_circle : Icons.warning,
                  size: 64,
                  color: isHealthy ? AppColors.success : AppColors.warning,
                ),
                const SizedBox(height: AppSpacing.md),
                Text(
                  _analysisResult!['disease_name_ar'],
                  style: AppTextStyles.h2.copyWith(
                    color: isHealthy ? AppColors.success : AppColors.warning,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'دقة التشخيص: $confidence%',
                  style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ),

        if (!isHealthy) ...[
          const SizedBox(height: AppSpacing.lg),

          // الأعراض
          _buildInfoCard(
            title: 'الأعراض',
            icon: Icons.medical_services,
            items: List<String>.from(_analysisResult!['symptoms']),
            color: AppColors.error,
          ),

          // العلاج
          _buildInfoCard(
            title: 'العلاج الموصى به',
            icon: Icons.healing,
            items: List<String>.from(_analysisResult!['treatment']),
            color: AppColors.success,
          ),

          // الوقاية
          _buildInfoCard(
            title: 'الوقاية المستقبلية',
            icon: Icons.shield,
            items: List<String>.from(_analysisResult!['prevention']),
            color: AppColors.info,
          ),
        ],
      ],
    );
  }

  Widget _buildInfoCard({
    required String title,
    required IconData icon,
    required List<String> items,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color),
                const SizedBox(width: AppSpacing.sm),
                Text(
                  title,
                  style: AppTextStyles.h3.copyWith(color: color),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            ...items.map((item) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('• ', style: TextStyle(color: color, fontSize: 20)),
                      Expanded(
                        child: Text(
                          item,
                          style: AppTextStyles.body1,
                        ),
                      ),
                    ],
                  ),
                )),
          ],
        ),
      ),
    );
  }
}
