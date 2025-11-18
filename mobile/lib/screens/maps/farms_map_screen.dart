import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';
import '../../models/farm.dart';
import '../../services/farm_service.dart';
import '../../utils/constants.dart';

class FarmsMapScreen extends StatefulWidget {
  const FarmsMapScreen({super.key});

  @override
  State<FarmsMapScreen> createState() => _FarmsMapScreenState();
}

class _FarmsMapScreenState extends State<FarmsMapScreen> {
  GoogleMapController? _mapController;
  Position? _currentPosition;
  Set<Marker> _markers = {};
  List<Farm> _farms = [];
  bool _isLoading = true;
  
  // الموقع الافتراضي (صنعاء، اليمن)
  static const LatLng _defaultLocation = LatLng(15.3694, 44.1910);

  @override
  void initState() {
    super.initState();
    _initializeMap();
  }

  Future<void> _initializeMap() async {
    await _getCurrentLocation();
    await _loadFarms();
  }

  Future<void> _getCurrentLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        setState(() {
          _isLoading = false;
        });
        return;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          setState(() {
            _isLoading = false;
          });
          return;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        setState(() {
          _isLoading = false;
        });
        return;
      }

      final position = await Geolocator.getCurrentPosition();
      setState(() {
        _currentPosition = position;
      });
    } catch (e) {
      print('خطأ في الحصول على الموقع: $e');
    }
  }

  Future<void> _loadFarms() async {
    try {
      final farmService = context.read<FarmService>();
      final farms = await farmService.getFarms();
      
      setState(() {
        _farms = farms;
        _createMarkers();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('فشل تحميل المزارع: ${e.toString()}'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  void _createMarkers() {
    _markers.clear();

    // إضافة علامة الموقع الحالي
    if (_currentPosition != null) {
      _markers.add(
        Marker(
          markerId: const MarkerId('current_location'),
          position: LatLng(
            _currentPosition!.latitude,
            _currentPosition!.longitude,
          ),
          icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
          infoWindow: const InfoWindow(
            title: 'موقعك الحالي',
          ),
        ),
      );
    }

    // إضافة علامات المزارع
    for (var farm in _farms) {
      if (farm.latitude != null && farm.longitude != null) {
        _markers.add(
          Marker(
            markerId: MarkerId('farm_${farm.id}'),
            position: LatLng(farm.latitude!, farm.longitude!),
            icon: BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
            infoWindow: InfoWindow(
              title: farm.name,
              snippet: '${farm.area} هكتار',
              onTap: () => _showFarmDetails(farm),
            ),
          ),
        );
      }
    }
  }

  void _showFarmDetails(Farm farm) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(AppBorderRadius.lg)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.4,
        minChildSize: 0.2,
        maxChildSize: 0.8,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // مؤشر السحب
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: AppSpacing.md),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // اسم المزرعة
              Text(
                farm.name,
                style: AppTextStyles.h2,
              ),
              const SizedBox(height: AppSpacing.sm),

              // الموقع
              Row(
                children: [
                  Icon(Icons.location_on, size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: AppSpacing.xs),
                  Expanded(
                    child: Text(
                      farm.location,
                      style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.md),

              // المعلومات
              _buildInfoRow('المساحة', '${farm.area} هكتار'),
              _buildInfoRow('نوع التربة', farm.soilType),
              if (farm.description != null) ...[
                const SizedBox(height: AppSpacing.md),
                Text(
                  'الوصف',
                  style: AppTextStyles.subtitle1,
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  farm.description!,
                  style: AppTextStyles.body2,
                ),
              ],

              const SizedBox(height: AppSpacing.lg),

              // أزرار الإجراءات
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => _openInMaps(farm),
                      icon: const Icon(Icons.directions),
                      label: const Text('الاتجاهات'),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        // الانتقال إلى تفاصيل المزرعة
                      },
                      icon: const Icon(Icons.info),
                      label: const Text('التفاصيل'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
          ),
          Text(
            value,
            style: AppTextStyles.body1.copyWith(fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  void _openInMaps(Farm farm) {
    // فتح في تطبيق الخرائط
    // يمكن استخدام url_launcher
  }

  void _goToCurrentLocation() {
    if (_currentPosition != null && _mapController != null) {
      _mapController!.animateCamera(
        CameraUpdate.newLatLngZoom(
          LatLng(_currentPosition!.latitude, _currentPosition!.longitude),
          15,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('خريطة المزارع'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadFarms,
            tooltip: 'تحديث',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : GoogleMap(
              initialCameraPosition: CameraPosition(
                target: _currentPosition != null
                    ? LatLng(_currentPosition!.latitude, _currentPosition!.longitude)
                    : _defaultLocation,
                zoom: 12,
              ),
              markers: _markers,
              myLocationEnabled: true,
              myLocationButtonEnabled: false,
              zoomControlsEnabled: false,
              mapToolbarEnabled: false,
              onMapCreated: (controller) {
                _mapController = controller;
              },
            ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          // زر الموقع الحالي
          FloatingActionButton(
            heroTag: 'current_location',
            onPressed: _goToCurrentLocation,
            backgroundColor: Colors.white,
            child: Icon(Icons.my_location, color: AppColors.primary),
          ),
          const SizedBox(height: AppSpacing.md),

          // زر إضافة مزرعة
          FloatingActionButton.extended(
            heroTag: 'add_farm',
            onPressed: () {
              // الانتقال إلى شاشة إضافة مزرعة
            },
            backgroundColor: AppColors.primary,
            icon: const Icon(Icons.add, color: Colors.white),
            label: const Text(
              'إضافة مزرعة',
              style: TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _mapController?.dispose();
    super.dispose();
  }
}
