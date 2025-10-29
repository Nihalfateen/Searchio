import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:searchio/widgets/text_widget.dart' show TextWidgetColors;


class HeaderWidget extends StatelessWidget {
  const HeaderWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(top: 100.h, bottom: 50.h,left: 130.w, right: 130.w),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.center,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          TextWidgetColors(
            'Searchio',
            style: TextStyle(
              fontSize: 80.sp,
              fontWeight: FontWeight.bold,
            ),
          ),

          SizedBox(height: 20.h),
          Container(
            padding: EdgeInsets.all(  10.h),
            decoration: BoxDecoration(
              boxShadow: const [
                BoxShadow(
                  color: Colors.black12,
                  blurRadius: 6,
                  offset: Offset(0, 3),
                ),
              ],
              borderRadius: BorderRadius.circular(30),
            ),
            child: SizedBox(
              width: 1000.w,
              
              child: TextFormField(
                textAlign: TextAlign.left,
                decoration: InputDecoration(
                  hintText: 'Search Searchio',
                  filled: true,
                  fillColor: Colors.white,
                  contentPadding: const EdgeInsets.symmetric(
                      vertical: 15.0, horizontal: 20.0),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(30.0),
                    borderSide: BorderSide.none,
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(30.0),
                    borderSide: BorderSide.none,
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(30.0),
                    borderSide:
                        const BorderSide(color: Colors.blueAccent, width: 1.5),
                  ),
                  suffixIcon: const Icon(Icons.search, color: Colors.grey),
                ),
              ),
            ),
          )
        ],
      ),
    );
  }
}