import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../models/iot_device.dart';
import '../utils/constants.dart';

class SensorChart extends StatelessWidget {
  final List<SensorReading> readings;
  final String sensorType;
  final String unit;

  const SensorChart({
    super.key,
    required this.readings,
    required this.sensorType,
    required this.unit,
  });

  @override
  Widget build(BuildContext context) {
    if (readings.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.show_chart,
              size: 64,
              color: AppColors.textSecondary.withOpacity(0.5),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              'لا توجد قراءات متاحة',
              style: AppTextStyles.body1.copyWith(color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(AppBorderRadius.md),
      ),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _getSensorTypeLabel(sensorType),
                  style: AppTextStyles.h3.copyWith(color: AppColors.textPrimary),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: AppSpacing.xs,
                  ),
                  decoration: BoxDecoration(
                    color: _getSensorColor(sensorType).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(AppBorderRadius.sm),
                  ),
                  child: Text(
                    '${readings.last.value.toStringAsFixed(1)} $unit',
                    style: AppTextStyles.body2.copyWith(
                      color: _getSensorColor(sensorType),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            SizedBox(
              height: 200,
              child: LineChart(
                LineChartData(
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: 1,
                    getDrawingHorizontalLine: (value) {
                      return FlLine(
                        color: Colors.grey[300]!,
                        strokeWidth: 1,
                      );
                    },
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        interval: 1,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() >= readings.length) {
                            return const Text('');
                          }
                          final reading = readings[value.toInt()];
                          return Padding(
                            padding: const EdgeInsets.only(top: 8.0),
                            child: Text(
                              _formatTime(reading.timestamp),
                              style: AppTextStyles.caption.copyWith(
                                color: AppColors.textSecondary,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        interval: _calculateInterval(),
                        reservedSize: 42,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toStringAsFixed(0),
                            style: AppTextStyles.caption.copyWith(
                              color: AppColors.textSecondary,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  borderData: FlBorderData(
                    show: true,
                    border: Border.all(color: Colors.grey[300]!),
                  ),
                  minX: 0,
                  maxX: (readings.length - 1).toDouble(),
                  minY: _getMinY(),
                  maxY: _getMaxY(),
                  lineBarsData: [
                    LineChartBarData(
                      spots: readings.asMap().entries.map((entry) {
                        return FlSpot(
                          entry.key.toDouble(),
                          entry.value.value,
                        );
                      }).toList(),
                      isCurved: true,
                      color: _getSensorColor(sensorType),
                      barWidth: 3,
                      isStrokeCapRound: true,
                      dotData: FlDotData(
                        show: true,
                        getDotPainter: (spot, percent, barData, index) {
                          return FlDotCirclePainter(
                            radius: 4,
                            color: _getSensorColor(sensorType),
                            strokeWidth: 2,
                            strokeColor: Colors.white,
                          );
                        },
                      ),
                      belowBarData: BarAreaData(
                        show: true,
                        color: _getSensorColor(sensorType).withOpacity(0.1),
                      ),
                    ),
                  ],
                  lineTouchData: LineTouchData(
                    touchTooltipData: LineTouchTooltipData(
                      getTooltipItems: (touchedSpots) {
                        return touchedSpots.map((spot) {
                          final reading = readings[spot.x.toInt()];
                          return LineTooltipItem(
                            '${reading.value.toStringAsFixed(1)} $unit\n${_formatDateTime(reading.timestamp)}',
                            const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getSensorTypeLabel(String type) {
    switch (type) {
      case 'temperature':
        return 'درجة الحرارة';
      case 'humidity':
        return 'الرطوبة';
      case 'soil_moisture':
        return 'رطوبة التربة';
      case 'ph':
        return 'حموضة التربة';
      case 'light':
        return 'الإضاءة';
      case 'rainfall':
        return 'الأمطار';
      default:
        return type;
    }
  }

  Color _getSensorColor(String type) {
    switch (type) {
      case 'temperature':
        return Colors.orange;
      case 'humidity':
        return Colors.blue;
      case 'soil_moisture':
        return Colors.brown;
      case 'ph':
        return Colors.purple;
      case 'light':
        return Colors.yellow[700]!;
      case 'rainfall':
        return Colors.lightBlue;
      default:
        return AppColors.primary;
    }
  }

  double _getMinY() {
    if (readings.isEmpty) return 0;
    final minValue = readings.map((r) => r.value).reduce((a, b) => a < b ? a : b);
    return (minValue - 5).floorToDouble();
  }

  double _getMaxY() {
    if (readings.isEmpty) return 100;
    final maxValue = readings.map((r) => r.value).reduce((a, b) => a > b ? a : b);
    return (maxValue + 5).ceilToDouble();
  }

  double _calculateInterval() {
    final range = _getMaxY() - _getMinY();
    if (range <= 20) return 5;
    if (range <= 50) return 10;
    if (range <= 100) return 20;
    return 50;
  }

  String _formatTime(DateTime dateTime) {
    return '${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}';
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day}/${dateTime.month} ${_formatTime(dateTime)}';
  }
}
