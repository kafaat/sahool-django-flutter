import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import '../models/irrigation_models.dart';
import '../providers/irrigation_provider.dart';
import '../widgets/irrigation_widgets.dart';
import './irrigation/schedule_screen.dart';
import './irrigation/history_screen.dart';
import './irrigation/settings_screen.dart';

class IrrigationScreen extends StatefulWidget {
  const IrrigationScreen({Key? key}) : super(key: key);

  @override
  _IrrigationScreenState createState() => _IrrigationScreenState();
}

class _IrrigationScreenState extends State<IrrigationScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    _loadIrrigationData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadIrrigationData() async {
    final provider = Provider.of<IrrigationProvider>(context, listen: false);
    await provider.loadIrrigationData();
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(localizations.irrigation),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(text: localizations.schedule),
            Tab(text: localizations.history),
            Tab(text: localizations.settings),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          IrrigationScheduleTab(),
          IrrigationHistoryTab(),
          IrrigationSettingsTab(),
        ],
      ),
    );
  }
}

class IrrigationScheduleTab extends StatefulWidget {
  @override
  _IrrigationScheduleTabState createState() => _IrrigationScheduleTabState();
}

class _IrrigationScheduleTabState extends State<IrrigationScheduleTab> {
  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Consumer<IrrigationProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading && provider.schedules.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }

        return RefreshIndicator(
          onRefresh: () => provider.loadIrrigationData(),
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: _buildScheduleHeader(provider, localizations, theme),
              ),
              SliverToBoxAdapter(
                child: _buildQuickActions(provider, localizations, theme),
              ),
              SliverToBoxAdapter(
                child: _buildActiveSchedules(provider, localizations, theme),
              ),
              SliverToBoxAdapter(
                child: _buildUpcomingSchedules(provider, localizations, theme),
              ),
              SliverToBoxAdapter(
                child: _buildRecommendedActions(provider, localizations, theme),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildScheduleHeader(
    IrrigationProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            theme.primaryColor,
            theme.primaryColor.withOpacity(0.7),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.irrigationSchedule,
            style: theme.textTheme.headlineSmall?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            localizations.manageYourIrrigationSchedule,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.white.withOpacity(0.9),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildScheduleStat(
                icon: Icons.water_drop,
                value: provider.activeSchedules.length.toString(),
                label: localizations.activeSchedules,
                color: Colors.white,
              ),
              _buildScheduleStat(
                icon: Icons.schedule,
                value: provider.nextIrrigation,
                label: localizations.nextIrrigation,
                color: Colors.white,
              ),
              _buildScheduleStat(
                icon: Icons.savings,
                value: '${provider.waterSaved}%',
                label: localizations.waterSaved,
                color: Colors.white,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildScheduleStat({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Column(
      children: [
        Icon(icon, color: color, size: 24),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: color.withOpacity(0.8),
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActions(
    IrrigationProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.quickActions,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildQuickActionCard(
                  icon: Icons.play_arrow,
                  title: localizations.startIrrigation,
                  subtitle: localizations.beginNow,
                  color: Colors.green,
                  onTap: () => _showStartIrrigationDialog(context, provider),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionCard(
                  icon: Icons.pause,
                  title: localizations.pauseIrrigation,
                  subtitle: localizations.stopCurrent,
                  color: Colors.orange,
                  onTap: () => _pauseIrrigation(provider),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _buildQuickActionCard(
                  icon: Icons.auto_mode,
                  title: localizations.autoMode,
                  subtitle: localizations.smartScheduling,
                  color: Colors.blue,
                  onTap: () => _toggleAutoMode(provider),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildQuickActionCard(
                  icon: Icons.water,
                  title: localizations.waterNow,
                  subtitle: localizations.manualControl,
                  color: Colors.teal,
                  onTap: () => _showWaterNowDialog(context, provider),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            children: [
              Icon(icon, color: color, size: 32),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 14,
                ),
                textAlign: TextAlign.center,
              ),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActiveSchedules(
    IrrigationProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    if (provider.activeSchedules.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.activeSchedules,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...provider.activeSchedules.map((schedule) => 
            _buildScheduleCard(schedule, localizations, theme)
          ).toList(),
        ],
      ),
    );
  }

  Widget _buildUpcomingSchedules(
    IrrigationProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    if (provider.upcomingSchedules.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.upcomingSchedules,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...provider.upcomingSchedules.map((schedule) => 
            _buildScheduleCard(schedule, localizations, theme, isUpcoming: true)
          ).toList(),
        ],
      ),
    );
  }

  Widget _buildScheduleCard(
    IrrigationSchedule schedule,
    AppLocalizations localizations,
    ThemeData theme, {
    bool isUpcoming = false,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8.0),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isUpcoming ? Colors.orange : Colors.green,
          child: Icon(
            isUpcoming ? Icons.schedule : Icons.water_drop,
            color: Colors.white,
          ),
        ),
        title: Text(schedule.fieldName),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${schedule.startTime} - ${schedule.endTime}'),
            Text('${schedule.waterAmount}L ${localizations.perHour}'),
            if (schedule.isSmartScheduled)
              Text(
                localizations.smartScheduled,
                style: const TextStyle(
                  color: Colors.blue,
                  fontSize: 12,
                ),
              ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (schedule.status == 'running')
              const Icon(Icons.play_arrow, color: Colors.green),
            if (schedule.status == 'pending')
              const Icon(Icons.schedule, color: Colors.orange),
            if (schedule.status == 'completed')
              const Icon(Icons.check, color: Colors.grey),
          ],
        ),
        onTap: () => _showScheduleDetails(context, schedule),
      ),
    );
  }

  Widget _buildRecommendedActions(
    IrrigationProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    if (provider.recommendations.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            localizations.recommendations,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 12),
          ...provider.recommendations.map((recommendation) => 
            _buildRecommendationCard(recommendation, localizations, theme)
          ).toList(),
        ],
      ),
    );
  }

  Widget _buildRecommendationCard(
    IrrigationRecommendation recommendation,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Card(
      color: _getRecommendationColor(recommendation.priority).withOpacity(0.1),
      child: ListTile(
        leading: Icon(
          _getRecommendationIcon(recommendation.type),
          color: _getRecommendationColor(recommendation.priority),
        ),
        title: Text(recommendation.title),
        subtitle: Text(recommendation.description),
        trailing: ElevatedButton(
          onPressed: () => _applyRecommendation(recommendation),
          child: Text(localizations.apply),
        ),
      ),
    );
  }

  Color _getRecommendationColor(String priority) {
    switch (priority) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  IconData _getRecommendationIcon(String type) {
    switch (type) {
      case 'water_shortage':
        return Icons.water_drop;
      case 'over_irrigation':
        return Icons.water;
      case 'weather_alert':
        return Icons.warning;
      case 'crop_needs':
        return Icons.grass;
      default:
        return Icons.info;
    }
  }

  // Action Methods
  void _showStartIrrigationDialog(BuildContext context, IrrigationProvider provider) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(AppLocalizations.of(context)!.startIrrigation),
          content: Text(AppLocalizations.of(context)!.selectFieldToIrrigate),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(AppLocalizations.of(context)!.cancel),
            ),
            ElevatedButton(
              onPressed: () {
                provider.startIrrigation();
                Navigator.pop(context);
              },
              child: Text(AppLocalizations.of(context)!.start),
            ),
          ],
        );
      },
    );
  }

  void _pauseIrrigation(IrrigationProvider provider) {
    provider.pauseIrrigation();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(AppLocalizations.of(context)!.irrigationPaused),
      ),
    );
  }

  void _toggleAutoMode(IrrigationProvider provider) {
    provider.toggleAutoMode();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          provider.isAutoMode
              ? AppLocalizations.of(context)!.autoModeEnabled
              : AppLocalizations.of(context)!.autoModeDisabled,
        ),
      ),
    );
  }

  void _showWaterNowDialog(BuildContext context, IrrigationProvider provider) {
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text(AppLocalizations.of(context)!.waterNow),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(AppLocalizations.of(context)!.enterWaterAmount),
              const SizedBox(height: 16),
              TextField(
                decoration: InputDecoration(
                  labelText: AppLocalizations.of(context)!.waterAmountL,
                  suffixText: 'L',
                ),
                keyboardType: TextInputType.number,
                onChanged: (value) {
                  // Store the value
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(AppLocalizations.of(context)!.cancel),
            ),
            ElevatedButton(
              onPressed: () {
                provider.waterNow(50); // Example amount
                Navigator.pop(context);
              },
              child: Text(AppLocalizations.of(context)!.water),
            ),
          ],
        );
      },
    );
  }

  void _showScheduleDetails(BuildContext context, IrrigationSchedule schedule) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ScheduleDetailScreen(schedule: schedule),
      ),
    );
  }

  void _applyRecommendation(IrrigationRecommendation recommendation) {
    final provider = Provider.of<IrrigationProvider>(context, listen: false);
    provider.applyRecommendation(recommendation);
  }
}

// Additional Tabs
class IrrigationHistoryTab extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Consumer<IrrigationProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading && provider.irrigationHistory.isEmpty) {
          return const Center(child: CircularProgressIndicator());
        }

        return ListView.builder(
          itemCount: provider.irrigationHistory.length,
          itemBuilder: (context, index) {
            final history = provider.irrigationHistory[index];
            return _buildHistoryCard(history, context);
          },
        );
      },
    );
  }

  Widget _buildHistoryCard(IrrigationHistory history, BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.all(8.0),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _getStatusColor(history.status),
          child: Icon(
            _getStatusIcon(history.status),
            color: Colors.white,
          ),
        ),
        title: Text(history.fieldName),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${history.startTime} - ${history.endTime}'),
            Text('${history.waterUsed}L ${localizations.used}'),
            Text('${localizations.by} ${history.executedBy}'),
          ],
        ),
        trailing: Text(
          _getStatusName(history.status, localizations),
          style: TextStyle(
            color: _getStatusColor(history.status),
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'failed':
        return Colors.red;
      case 'cancelled':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  IconData _getStatusIcon(String status) {
    switch (status) {
      case 'completed':
        return Icons.check;
      case 'failed':
        return Icons.error;
      case 'cancelled':
        return Icons.cancel;
      default:
        return Icons.help;
    }
  }

  String _getStatusName(String status, AppLocalizations localizations) {
    switch (status) {
      case 'completed':
        return localizations.completed;
      case 'failed':
        return localizations.failed;
      case 'cancelled':
        return localizations.cancelled;
      default:
        return status;
    }
  }
}

class IrrigationSettingsTab extends StatefulWidget {
  @override
  _IrrigationSettingsTabState createState() => _IrrigationSettingsTabState();
}

class _IrrigationSettingsTabState extends State<IrrigationSettingsTab> {
  bool _autoMode = false;
  double _waterThreshold = 30.0;
  int _scheduleInterval = 24;

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;

    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        _buildSettingsSection(
          title: localizations.automationSettings,
          children: [
            SwitchListTile(
              title: Text(localizations.enableAutoMode),
              subtitle: Text(localizations.allowSmartScheduling),
              value: _autoMode,
              onChanged: (value) {
                setState(() {
                  _autoMode = value;
                });
              },
            ),
          ],
        ),
        _buildSettingsSection(
          title: localizations.waterThresholds,
          children: [
            ListTile(
              title: Text(localizations.soilMoistureThreshold),
              subtitle: Text('$_waterThreshold%'),
              trailing: Slider(
                value: _waterThreshold,
                min: 10,
                max: 80,
                divisions: 14,
                label: '$_waterThreshold%',
                onChanged: (value) {
                  setState(() {
                    _waterThreshold = value;
                  });
                },
              ),
            ),
          ],
        ),
        _buildSettingsSection(
          title: localizations.scheduleSettings,
          children: [
            ListTile(
              title: Text(localizations.scheduleInterval),
              subtitle: Text('$_scheduleInterval ${localizations.hours}'),
              trailing: DropdownButton<int>(
                value: _scheduleInterval,
                items: [6, 12, 24, 48, 72].map((int value) {
                  return DropdownMenuItem<int>(
                    value: value,
                    child: Text('$value ${localizations.hours}'),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() {
                      _scheduleInterval = value;
                    });
                  }
                },
              ),
            ),
          ],
        ),
        _buildSettingsSection(
          title: localizations.notifications,
          children: [
            SwitchListTile(
              title: Text(localizations.irrigationAlerts),
              subtitle: Text(localizations.getNotifiedWhenIrrigationStarts),
              value: true,
              onChanged: (value) {
                // Save setting
              },
            ),
            SwitchListTile(
              title: Text(localizations.lowWaterAlerts),
              subtitle: Text(localizations.getNotifiedWhenWaterIsLow),
              value: true,
              onChanged: (value) {
                // Save setting
              },
            ),
          ],
        ),
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: ElevatedButton(
            onPressed: () {
              _saveSettings();
            },
            child: Text(localizations.saveSettings),
          ),
        ),
      ],
    );
  }

  Widget _buildSettingsSection({
    required String title,
    required List<Widget> children,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          ...children,
        ],
      ),
    );
  }

  void _saveSettings() {
    // Save settings to provider
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(AppLocalizations.of(context)!.settingsSaved),
      ),
    );
  }
}