import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import '../models/field_models.dart';
import '../providers/field_provider.dart';
import '../widgets/field_widgets.dart';
import './fields/field_detail_screen.dart';
import './fields/add_field_screen.dart';
import './fields/edit_field_screen.dart';

class FieldsScreen extends StatefulWidget {
  const FieldsScreen({Key? key}) : super(key: key);

  @override
  _FieldsScreenState createState() => _FieldsScreenState();
}

class _FieldsScreenState extends State<FieldsScreen> {
  String _selectedFarmId = 'all';
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadFieldsData();
  }

  Future<void> _loadFieldsData() async {
    final provider = Provider.of<FieldProvider>(context, listen: false);
    await provider.loadFields();
  }

  void _onFarmSelected(String farmId) {
    setState(() {
      _selectedFarmId = farmId;
    });
    final provider = Provider.of<FieldProvider>(context, listen: false);
    provider.filterFieldsByFarm(farmId);
  }

  void _onSearchChanged(String query) {
    setState(() {
      _searchQuery = query;
    });
    final provider = Provider.of<FieldProvider>(context, listen: false);
    provider.searchFields(query);
  }

  void _navigateToFieldDetail(Field field) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => FieldDetailScreen(field: field),
      ),
    );
  }

  void _navigateToAddField() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const AddFieldScreen(),
      ),
    );
  }

  void _navigateToEditField(Field field) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => EditFieldScreen(field: field),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(localizations.fields),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _navigateToAddField,
            tooltip: localizations.addField,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadFieldsData,
        child: Consumer<FieldProvider>(
          builder: (context, provider, child) {
            if (provider.isLoading && provider.fields.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }

            if (provider.fields.isEmpty) {
              return _buildEmptyState(localizations);
            }

            return _buildFieldsContent(provider, localizations, theme);
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _navigateToAddField,
        child: const Icon(Icons.add),
        tooltip: localizations.addNewField,
      ),
    );
  }

  Widget _buildEmptyState(AppLocalizations localizations) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.agriculture_outlined,
            size: 100,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            localizations.noFieldsAvailable,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            localizations.startByAddingField,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[500],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _navigateToAddField,
            icon: const Icon(Icons.add),
            label: Text(localizations.addFirstField),
          ),
        ],
      ),
    );
  }

  Widget _buildFieldsContent(
    FieldProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Column(
      children: [
        // Search and Filter Section
        _buildSearchAndFilterSection(provider, localizations, theme),
        
        // Fields Statistics
        _buildFieldsStats(provider, localizations, theme),
        
        // Fields Grid
        Expanded(
          child: _buildFieldsGrid(provider, localizations, theme),
        ),
      ],
    );
  }

  Widget _buildSearchAndFilterSection(
    FieldProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      color: theme.cardColor,
      child: Column(
        children: [
          // Search Bar
          TextField(
            decoration: InputDecoration(
              hintText: localizations.searchFields,
              prefixIcon: const Icon(Icons.search),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(25),
              ),
              filled: true,
              fillColor: theme.scaffoldBackgroundColor,
            ),
            onChanged: _onSearchChanged,
          ),
          const SizedBox(height: 16),
          // Farm Filter
          Row(
            children: [
              Text(
                '${localizations.filterByFarm}:',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: DropdownButtonFormField<String>(
                  value: _selectedFarmId,
                  decoration: InputDecoration(
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                  ),
                  items: [
                    DropdownMenuItem(
                      value: 'all',
                      child: Text(localizations.allFarms),
                    ),
                    ...provider.farms.map((farm) {
                      return DropdownMenuItem(
                        value: farm.id,
                        child: Text(farm.name),
                      );
                    }).toList(),
                  ],
                  onChanged: (value) {
                    if (value != null) {
                      _onFarmSelected(value);
                    }
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFieldsStats(
    FieldProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return Container(
      padding: const EdgeInsets.all(16.0),
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStatCard(
            icon: Icons.agriculture,
            value: provider.totalFields.toString(),
            label: localizations.totalFields,
            color: Colors.green,
          ),
          _buildStatCard(
            icon: Icons.landscape,
            value: '${provider.totalArea.toStringAsFixed(1)}m²',
            label: localizations.totalArea,
            color: Colors.blue,
          ),
          _buildStatCard(
            icon: Icons.crop_square,
            value: provider.averageArea.toStringAsFixed(1),
            label: localizations.avgFieldArea,
            color: Colors.orange,
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String value,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              color: color.withOpacity(0.8),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFieldsGrid(
    FieldProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return GridView.builder(
      padding: const EdgeInsets.all(16.0),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 0.85,
      ),
      itemCount: provider.fields.length,
      itemBuilder: (context, index) {
        final field = provider.fields[index];
        return FieldCard(
          field: field,
          onTap: () => _navigateToFieldDetail(field),
          onEdit: () => _navigateToEditField(field),
        );
      },
    );
  }
}

// Widgets for Fields Screen
class FieldCard extends StatelessWidget {
  final Field field;
  final VoidCallback onTap;
  final VoidCallback onEdit;

  const FieldCard({
    Key? key,
    required this.field,
    required this.onTap,
    required this.onEdit,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final localizations = AppLocalizations.of(context)!;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with Status and Actions
            Container(
              padding: const EdgeInsets.all(8.0),
              decoration: BoxDecoration(
                color: _getStatusColor(field.status).withOpacity(0.1),
                borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 2,
                    ),
                    decoration: BoxDecoration(
                      color: _getStatusColor(field.status),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      _getStatusName(field.status, localizations),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      if (value == 'edit') {
                        onEdit();
                      }
                    },
                    itemBuilder: (context) => [
                      PopupMenuItem(
                        value: 'edit',
                        child: Text(localizations.edit),
                      ),
                      PopupMenuItem(
                        value: 'delete',
                        child: Text(localizations.delete),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            // Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    // Field Name and Farm
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          field.name,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Text(
                          field.farm.name,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: Colors.grey,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                    // Field Details
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.straighten, size: 16, color: Colors.grey),
                            const SizedBox(width: 4),
                            Text(
                              '${field.area} m²',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.crop, size: 16, color: Colors.grey),
                            const SizedBox(width: 4),
                            Text(
                              '${field.totalCrops} ${localizations.crops}',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            const Icon(Icons.water, size: 16, color: Colors.grey),
                            const SizedBox(width: 4),
                            Text(
                              '${field.soilType}',
                              style: theme.textTheme.bodySmall,
                            ),
                          ],
                        ),
                      ],
                    ),
                    // Health Score
                    if (field.healthScore > 0)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: 8),
                          Text(
                            localizations.healthScore,
                            style: theme.textTheme.bodySmall,
                          ),
                          const SizedBox(height: 2),
                          LinearProgressIndicator(
                            value: field.healthScore / 100,
                            backgroundColor: Colors.grey[200],
                            valueColor: AlwaysStoppedAnimation<Color>(
                              _getHealthColor(field.healthScore),
                            ),
                            minHeight: 4,
                          ),
                          Text(
                            '${field.healthScore.toStringAsFixed(0)}%',
                            style: theme.textTheme.bodySmall?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'active':
        return Colors.green;
      case 'inactive':
        return Colors.red;
      case 'maintenance':
        return Colors.orange;
      case 'planning':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  String _getStatusName(String status, AppLocalizations localizations) {
    switch (status) {
      case 'active':
        return localizations.active;
      case 'inactive':
        return localizations.inactive;
      case 'maintenance':
        return localizations.maintenance;
      case 'planning':
        return localizations.planning;
      default:
        return status;
    }
  }

  Color _getHealthColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    if (score >= 40) return Colors.yellow;
    return Colors.red;
  }
}