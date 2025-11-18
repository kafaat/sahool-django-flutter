import 'package:flutter/material.dart';

/// شاشة Marketplace - سوق المحاصيل
class MarketplaceScreen extends StatefulWidget {
  const MarketplaceScreen({Key? key}) : super(key: key);

  @override
  State<MarketplaceScreen> createState() => _MarketplaceScreenState();
}

class _MarketplaceScreenState extends State<MarketplaceScreen> {
  String _selectedCategory = 'الكل';
  final List<String> _categories = [
    'الكل',
    'خضروات',
    'فواكه',
    'حبوب',
    'بقوليات',
  ];

  // بيانات تجريبية
  final List<Map<String, dynamic>> _listings = [
    {
      'id': 1,
      'title': 'طماطم طازجة',
      'seller': 'محمد أحمد',
      'price': 5.0,
      'unit': 'كجم',
      'quantity': 500,
      'location': 'صنعاء',
      'image': 'assets/tomato.jpg',
      'quality': 'ممتاز',
    },
    {
      'id': 2,
      'title': 'خيار أخضر',
      'seller': 'علي حسن',
      'price': 3.5,
      'unit': 'كجم',
      'quantity': 300,
      'location': 'تعز',
      'image': 'assets/cucumber.jpg',
      'quality': 'درجة أولى',
    },
    {
      'id': 3,
      'title': 'بطاطس',
      'seller': 'سعيد محمود',
      'price': 4.0,
      'unit': 'كجم',
      'quantity': 1000,
      'location': 'إب',
      'image': 'assets/potato.jpg',
      'quality': 'ممتاز',
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('سوق المحاصيل'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              // TODO: تنفيذ البحث
            },
          ),
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () {
              // TODO: تنفيذ الفلترة
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // شريط الفئات
          Container(
            height: 50,
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _categories.length,
              itemBuilder: (context, index) {
                final category = _categories[index];
                final isSelected = category == _selectedCategory;
                
                return Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: ChoiceChip(
                    label: Text(category),
                    selected: isSelected,
                    onSelected: (selected) {
                      setState(() {
                        _selectedCategory = category;
                      });
                    },
                  ),
                );
              },
            ),
          ),
          
          // قائمة الإعلانات
          Expanded(
            child: RefreshIndicator(
              onRefresh: () async {
                // TODO: تحديث البيانات
                await Future.delayed(const Duration(seconds: 1));
              },
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _listings.length,
                itemBuilder: (context, index) {
                  final listing = _listings[index];
                  return _buildListingCard(listing);
                },
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // TODO: الانتقال إلى شاشة إضافة إعلان
        },
        icon: const Icon(Icons.add),
        label: const Text('إعلان جديد'),
      ),
    );
  }

  Widget _buildListingCard(Map<String, dynamic> listing) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: InkWell(
        onTap: () {
          // TODO: الانتقال إلى تفاصيل الإعلان
        },
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // صورة المنتج
            Container(
              height: 200,
              decoration: BoxDecoration(
                color: Colors.grey[300],
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(12),
                ),
              ),
              child: Center(
                child: Icon(
                  Icons.image,
                  size: 64,
                  color: Colors.grey[400],
                ),
              ),
            ),
            
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // العنوان والجودة
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        listing['title'],
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.green[100],
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          listing['quality'],
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.green[800],
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 8),
                  
                  // البائع والموقع
                  Row(
                    children: [
                      const Icon(Icons.person, size: 16, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        listing['seller'],
                        style: const TextStyle(color: Colors.grey),
                      ),
                      const SizedBox(width: 16),
                      const Icon(Icons.location_on, size: 16, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text(
                        listing['location'],
                        style: const TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // السعر والكمية
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'السعر',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey,
                            ),
                          ),
                          Text(
                            '${listing['price']} ريال/${listing['unit']}',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: Colors.green,
                            ),
                          ),
                        ],
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          const Text(
                            'الكمية المتوفرة',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey,
                            ),
                          ),
                          Text(
                            '${listing['quantity']} ${listing['unit']}',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 12),
                  
                  // أزرار الإجراءات
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: () {
                            // TODO: الاتصال بالبائع
                          },
                          icon: const Icon(Icons.phone),
                          label: const Text('اتصال'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: () {
                            // TODO: تقديم عرض
                          },
                          icon: const Icon(Icons.local_offer),
                          label: const Text('تقديم عرض'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
