import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import '../models/marketplace_models.dart';
import '../providers/marketplace_provider.dart';
import '../widgets/marketplace_widgets.dart';
import './marketplace/listing_detail_screen.dart';
import './marketplace/add_listing_screen.dart';
import './marketplace/my_listings_screen.dart';

class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({Key? key}) : super(key: key);

  @override
  _MarketplaceScreenState createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen> {
  final ScrollController _scrollController = ScrollController();
  String _selectedCategory = 'all';
  String _searchQuery = '';
  bool _isLoadingMore = false;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    _loadMarketplaceData();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels == _scrollController.position.maxScrollExtent &&
        !_isLoadingMore) {
      _loadMoreListings();
    }
  }

  Future<void> _loadMarketplaceData() async {
    final provider = Provider.of<MarketplaceProvider>(context, listen: false);
    await provider.loadMarketplaceOverview();
  }

  Future<void> _loadMoreListings() async {
    setState(() => _isLoadingMore = true);
    final provider = Provider.of<MarketplaceProvider>(context, listen: false);
    await provider.loadMoreListings();
    setState(() => _isLoadingMore = false);
  }

  void _onCategorySelected(String category) {
    setState(() {
      _selectedCategory = category;
    });
    final provider = Provider.of<MarketplaceProvider>(context, listen: false);
    provider.filterListingsByCategory(category);
  }

  void _onSearchChanged(String query) {
    setState(() {
      _searchQuery = query;
    });
    final provider = Provider.of<MarketplaceProvider>(context, listen: false);
    provider.searchListings(query);
  }

  void _navigateToListingDetail(CropListing listing) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ListingDetailScreen(listing: listing),
      ),
    );
  }

  void _navigateToAddListing() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const AddListingScreen(),
      ),
    );
  }

  void _navigateToMyListings() {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => const MyListingsScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final localizations = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(localizations.marketplace),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_business),
            onPressed: _navigateToAddListing,
            tooltip: localizations.addListing,
          ),
          IconButton(
            icon: const Icon(Icons.list_alt),
            onPressed: _navigateToMyListings,
            tooltip: localizations.myListings,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadMarketplaceData,
        child: Consumer<MarketplaceProvider>(
          builder: (context, provider, child) {
            if (provider.isLoading && provider.listings.isEmpty) {
              return const Center(child: CircularProgressIndicator());
            }

            if (provider.listings.isEmpty) {
              return _buildEmptyState(localizations);
            }

            return _buildMarketplaceContent(provider, localizations, theme);
          },
        ),
      ),
    );
  }

  Widget _buildEmptyState(AppLocalizations localizations) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.store_mall_directory_outlined,
            size: 100,
            color: Colors.grey[400],
          ),
          const SizedBox(height: 16),
          Text(
            localizations.noListingsAvailable,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            localizations.beTheFirstToList,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[500],
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: _navigateToAddListing,
            icon: const Icon(Icons.add),
            label: Text(localizations.addFirstListing),
          ),
        ],
      ),
    );
  }

  Widget _buildMarketplaceContent(
    MarketplaceProvider provider,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    return CustomScrollView(
      controller: _scrollController,
      slivers: [
        SliverToBoxAdapter(
          child: _buildSearchAndFilterSection(localizations, theme),
        ),
        SliverToBoxAdapter(
          child: _buildMarketplaceStats(provider, localizations, theme),
        ),
        SliverToBoxAdapter(
          child: _buildFeaturedListings(provider.featuredListings, localizations, theme),
        ),
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Text(
              localizations.allListings,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        SliverPadding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          sliver: SliverGrid(
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 0.8,
            ),
            delegate: SliverChildBuilderDelegate(
              (context, index) {
                if (index >= provider.listings.length) {
                  return _buildLoadingIndicator();
                }
                
                final listing = provider.listings[index];
                return ListingCard(
                  listing: listing,
                  onTap: () => _navigateToListingDetail(listing),
                );
              },
              childCount: provider.listings.length + (_isLoadingMore ? 1 : 0),
            ),
          ),
        ),
        if (_isLoadingMore)
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Center(
                child: CircularProgressIndicator(),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildSearchAndFilterSection(
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
              hintText: localizations.searchListings,
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
          // Category Filter
          SizedBox(
            height: 40,
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                _buildCategoryChip(localizations.all, 'all'),
                _buildCategoryChip(localizations.vegetables, 'vegetables'),
                _buildCategoryChip(localizations.fruits, 'fruits'),
                _buildCategoryChip(localizations.grains, 'grains'),
                _buildCategoryChip(localizations.herbs, 'herbs'),
                _buildCategoryChip(localizations.flowers, 'flowers'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCategoryChip(String label, String category) {
    final isSelected = _selectedCategory == category;
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: ChoiceChip(
        label: Text(label),
        selected: isSelected,
        onSelected: (selected) {
          if (selected) {
            _onCategorySelected(category);
          }
        },
      ),
    );
  }

  Widget _buildMarketplaceStats(
    MarketplaceProvider provider,
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
            icon: Icons.store,
            value: provider.totalListings.toString(),
            label: localizations.activeListings,
            color: Colors.blue,
          ),
          _buildStatCard(
            icon: Icons.category,
            value: provider.totalCategories.toString(),
            label: localizations.categories,
            color: Colors.green,
          ),
          _buildStatCard(
            icon: Icons.people,
            value: provider.activeUsers.toString(),
            label: localizations.activeUsers,
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
      ),
    );
  }

  Widget _buildFeaturedListings(
    List<CropListing> featuredListings,
    AppLocalizations localizations,
    ThemeData theme,
  ) {
    if (featuredListings.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
      height: 200,
      margin: const EdgeInsets.symmetric(vertical: 16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Text(
              localizations.featuredListings,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              itemCount: featuredListings.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.only(right: 12.0),
                  child: FeaturedListingCard(
                    listing: featuredListings[index],
                    onTap: () => _navigateToListingDetail(featuredListings[index]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(16.0),
        child: CircularProgressIndicator(),
      ),
    );
  }
}

// Widgets for Marketplace Screen
class ListingCard extends StatelessWidget {
  final CropListing listing;
  final VoidCallback onTap;

  const ListingCard({
    Key? key,
    required this.listing,
    required this.onTap,
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
            // Image
            ClipRRect(
              borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
              child: listing.images.isNotEmpty
                  ? Image.network(
                      listing.images.first,
                      height: 120,
                      width: double.infinity,
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(
                          height: 120,
                          color: Colors.grey[200],
                          child: const Icon(Icons.image, size: 48, color: Colors.grey),
                        );
                      },
                    )
                  : Container(
                      height: 120,
                      color: Colors.grey[200],
                      child: const Icon(Icons.image, size: 48, color: Colors.grey),
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
                    // Title and Category
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          listing.crop.name,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: theme.primaryColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            _getCategoryName(listing.crop.category, localizations),
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.primaryColor,
                              fontSize: 10,
                            ),
                          ),
                        ),
                      ],
                    ),
                    // Price and Seller
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${listing.pricePerUnit} ${listing.currency}/${listing.unit}',
                          style: theme.textTheme.titleMedium?.copyWith(
                            color: theme.colorScheme.secondary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          '${localizations.by} ${listing.seller.username}',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: Colors.grey,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
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

  String _getCategoryName(String category, AppLocalizations localizations) {
    switch (category) {
      case 'vegetables':
        return localizations.vegetables;
      case 'fruits':
        return localizations.fruits;
      case 'grains':
        return localizations.grains;
      case 'herbs':
        return localizations.herbs;
      case 'flowers':
        return localizations.flowers;
      default:
        return category;
    }
  }
}

class FeaturedListingCard extends StatelessWidget {
  final CropListing listing;
  final VoidCallback onTap;

  const FeaturedListingCard({
    Key? key,
    required this.listing,
    required this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: 160,
      child: Card(
        elevation: 4,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Image with Featured Badge
              Stack(
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(16)),
                    child: listing.images.isNotEmpty
                        ? Image.network(
                            listing.images.first,
                            height: 100,
                            width: double.infinity,
                            fit: BoxFit.cover,
                          )
                        : Container(
                            height: 100,
                            color: Colors.grey[200],
                            child: const Icon(Icons.image, size: 48, color: Colors.grey),
                          ),
                  ),
                  Positioned(
                    top: 8,
                    left: 8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.amber,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Text(
                        'مميز',
                        style: TextStyle(
                          color: Colors.black,
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              // Content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(12.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        listing.crop.name,
                        style: theme.textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      Text(
                        '${listing.pricePerUnit} ${listing.currency}',
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: theme.colorScheme.secondary,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}