import 'package:flutter/material.dart';
import '../../models/farm.dart';
import '../../utils/constants.dart';
import 'add_edit_farm_screen.dart';

class FarmDetailScreen extends StatefulWidget {
  final Farm farm;

  const FarmDetailScreen({super.key, required this.farm});

  @override
  State<FarmDetailScreen> createState() => _FarmDetailScreenState();
}

class _FarmDetailScreenState extends State<FarmDetailScreen> {
  late Farm _farm;

  @override
  void initState() {
    super.initState();
    _farm = widget.farm;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_farm.name),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () async {
              final result = await Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => AddEditFarmScreen(farm: _farm),
                ),
              );
              
              if (result == true && mounted) {
                // إعادة تحميل البيانات
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('تم التحديث بنجاح')),
                );
              }
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // صورة رأسية (placeholder)
            Container(
              height: 200,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [AppColors.primary, AppColors.primaryDark],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              child: const Center(
                child: Icon(
                  Icons.agriculture,
                  size: 80,
                  color: Colors.white,
                ),
              ),
            ),

            // معلومات المزرعة
            Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // اسم المزرعة
                  Text(
                    _farm.name,
                    style: AppTextStyles.h1.copyWith(color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.sm),

                  // الموقع
                  if (_farm.location != null) ...[
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 20, color: AppColors.textSecondary),
                        const SizedBox(width: AppSpacing.xs),
                        Text(
                          _farm.location!,
                          style: AppTextStyles.body1.copyWith(color: AppColors.textSecondary),
                        ),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.md),
                  ],

                  const Divider(),
                  const SizedBox(height: AppSpacing.md),

                  // الإحصائيات
                  Text(
                    'الإحصائيات',
                    style: AppTextStyles.h3.copyWith(color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  Row(
                    children: [
                      Expanded(
                        child: _buildStatCard(
                          icon: Icons.straighten,
                          title: 'المساحة',
                          value: _farm.totalArea != null 
                              ? '${_farm.totalArea!.toStringAsFixed(1)} هكتار'
                              : 'غير محدد',
                          color: AppColors.primary,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: _buildStatCard(
                          icon: Icons.landscape,
                          title: 'الحقول',
                          value: '${_farm.fieldsCount ?? 0}',
                          color: AppColors.secondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.md),

                  Row(
                    children: [
                      Expanded(
                        child: _buildStatCard(
                          icon: Icons.grass,
                          title: 'المحاصيل',
                          value: '${_farm.cropsCount ?? 0}',
                          color: AppColors.success,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: _buildStatCard(
                          icon: Icons.devices,
                          title: 'الأجهزة',
                          value: '${_farm.devicesCount ?? 0}',
                          color: AppColors.info,
                        ),
                      ),
                    ],
                  ),

                  if (_farm.description != null) ...[
                    const SizedBox(height: AppSpacing.lg),
                    const Divider(),
                    const SizedBox(height: AppSpacing.md),
                    Text(
                      'الوصف',
                      style: AppTextStyles.h3.copyWith(color: AppColors.textPrimary),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      _farm.description!,
                      style: AppTextStyles.body1.copyWith(color: AppColors.textSecondary),
                    ),
                  ],

                  const SizedBox(height: AppSpacing.lg),
                  const Divider(),
                  const SizedBox(height: AppSpacing.md),

                  // أزرار الإجراءات
                  Text(
                    'الإجراءات السريعة',
                    style: AppTextStyles.h3.copyWith(color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.md),

                  _buildActionButton(
                    icon: Icons.add,
                    title: 'إضافة حقل جديد',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('قريباً: إضافة حقل')),
                      );
                    },
                  ),
                  _buildActionButton(
                    icon: Icons.grass,
                    title: 'إضافة محصول',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('قريباً: إضافة محصول')),
                      );
                    },
                  ),
                  _buildActionButton(
                    icon: Icons.bar_chart,
                    title: 'عرض التقارير',
                    onTap: () {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('قريباً: التقارير')),
                      );
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String title,
    required String value,
    required Color color,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorderRadius.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: AppSpacing.sm),
            Text(
              value,
              style: AppTextStyles.h3.copyWith(color: AppColors.textPrimary),
            ),
            Text(
              title,
              style: AppTextStyles.caption.copyWith(color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorderRadius.md),
      ),
      child: ListTile(
        leading: Icon(icon, color: AppColors.primary),
        title: Text(title, style: AppTextStyles.body1),
        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
        onTap: onTap,
      ),
    );
  }
}
