import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/farm.dart';
import '../../services/farm_service.dart';
import '../../utils/constants.dart';

class AddEditFarmScreen extends StatefulWidget {
  final Farm? farm; // null للإضافة، غير null للتعديل

  const AddEditFarmScreen({super.key, this.farm});

  @override
  State<AddEditFarmScreen> createState() => _AddEditFarmScreenState();
}

class _AddEditFarmScreenState extends State<AddEditFarmScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _locationController = TextEditingController();
  final _totalAreaController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  bool _isLoading = false;
  bool get _isEditMode => widget.farm != null;

  @override
  void initState() {
    super.initState();
    if (_isEditMode) {
      _nameController.text = widget.farm!.name;
      _locationController.text = widget.farm!.location ?? '';
      _totalAreaController.text = widget.farm!.totalArea?.toString() ?? '';
      _descriptionController.text = widget.farm!.description ?? '';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _locationController.dispose();
    _totalAreaController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _saveFarm() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    try {
      final farmService = FarmService(context.read());
      
      final farmData = {
        'name': _nameController.text,
        'location': _locationController.text,
        'total_area': double.tryParse(_totalAreaController.text),
        'description': _descriptionController.text,
      };

      if (_isEditMode) {
        await farmService.updateFarm(widget.farm!.id, farmData);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('تم تحديث المزرعة بنجاح'),
              backgroundColor: AppColors.success,
            ),
          );
        }
      } else {
        await farmService.createFarm(farmData);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('تم إضافة المزرعة بنجاح'),
              backgroundColor: AppColors.success,
            ),
          );
        }
      }

      if (mounted) {
        Navigator.of(context).pop(true); // إرجاع true للإشارة إلى النجاح
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('حدث خطأ: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isEditMode ? 'تعديل المزرعة' : 'إضافة مزرعة جديدة'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // اسم المزرعة
                TextFormField(
                  controller: _nameController,
                  decoration: InputDecoration(
                    labelText: 'اسم المزرعة *',
                    prefixIcon: const Icon(Icons.agriculture),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppBorderRadius.md),
                    ),
                    filled: true,
                    fillColor: Colors.grey[50],
                  ),
                  validator: (value) =>
                      value?.isEmpty ?? true ? 'الرجاء إدخال اسم المزرعة' : null,
                ),
                const SizedBox(height: AppSpacing.md),

                // الموقع
                TextFormField(
                  controller: _locationController,
                  decoration: InputDecoration(
                    labelText: 'الموقع',
                    prefixIcon: const Icon(Icons.location_on),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppBorderRadius.md),
                    ),
                    filled: true,
                    fillColor: Colors.grey[50],
                  ),
                ),
                const SizedBox(height: AppSpacing.md),

                // المساحة الإجمالية
                TextFormField(
                  controller: _totalAreaController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    labelText: 'المساحة الإجمالية (هكتار)',
                    prefixIcon: const Icon(Icons.straighten),
                    suffixText: 'هكتار',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppBorderRadius.md),
                    ),
                    filled: true,
                    fillColor: Colors.grey[50],
                  ),
                  validator: (value) {
                    if (value?.isNotEmpty ?? false) {
                      final number = double.tryParse(value!);
                      if (number == null || number <= 0) {
                        return 'الرجاء إدخال رقم صحيح';
                      }
                    }
                    return null;
                  },
                ),
                const SizedBox(height: AppSpacing.md),

                // الوصف
                TextFormField(
                  controller: _descriptionController,
                  maxLines: 4,
                  decoration: InputDecoration(
                    labelText: 'الوصف',
                    prefixIcon: const Icon(Icons.description),
                    alignLabelWithHint: true,
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(AppBorderRadius.md),
                    ),
                    filled: true,
                    fillColor: Colors.grey[50],
                  ),
                ),
                const SizedBox(height: AppSpacing.xl),

                // أزرار الحفظ والإلغاء
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
                        style: OutlinedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppBorderRadius.md),
                          ),
                        ),
                        child: const Text('إلغاء'),
                      ),
                    ),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _saveFarm,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(AppBorderRadius.md),
                          ),
                        ),
                        child: _isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  color: Colors.white,
                                  strokeWidth: 2,
                                ),
                              )
                            : Text(
                                _isEditMode ? 'حفظ التعديلات' : 'إضافة المزرعة',
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
