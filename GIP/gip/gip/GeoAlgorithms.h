/*
 * gip_GeoAlgorithms.h
 *
 *  Created on: Aug 26, 2011
 *      Author: mhanson
 */

#ifndef GIP_GEOALGORITHMS_H
#define GIP_GEOALGORITHMS_H

#include <gip/GeoImage.h>
#include <gip/GeoRaster.h>

namespace gip {

    //! Create a mask of NoData values
	GeoRaster CreateMask(const GeoImage&, std::string);

    // TODO - Rad and Ref can be combined into some sort of product
    //! Calculate and output radiance
	GeoImage Rad(const GeoImage&, std::string);

    //! Calculate and output reflectance
	GeoImage Ref(const GeoImage&, std::string);

	//! Stretch image into byte
	GeoImage RGB(const GeoImage&, std::string);

    //! Create single image from multiple input images using vector file footprint
	GeoImage CookieCutter(std::vector<std::string>, std::string, std::string, float=1.0, float=1.0);

	GeoImage NDVI(const GeoImage&, std::string);
	GeoImage EVI(const GeoImage&, std::string);
	GeoImage LSWI(const GeoImage&, std::string);
	GeoImage NDSI(const GeoImage&, std::string);
	GeoImage SATVI(const GeoImage&, std::string);

	//! Create new file of standard indices: NDVI, EVI, LSWI, NDSI, BI
	GeoImage Indices(const GeoImage&, std::string, bool=true, bool=true, bool=true, bool=true, bool=true);

	//! Create new file with AutoCloud algorithm
	GeoImage AutoCloud(const GeoImage&, std::string, int=4000, float=0.2, float=14, float=0.2, int=20);

	//! Create new file with a basic cloud mask
	GeoImage Fmask(const GeoImage&, std::string, int=3, int=5);


    //! Rescale indices (between lo and hi) to between 0 and 1
    GeoImage Index2Probability(const GeoImage&, std::string, float, float);

	//! Kmeans
	GeoImage kmeans(const GeoImage&, std::string, int classes=5, int iterations=5, float threshold=1.0);


    //GeoImage BandMath(const GeoImage&, std::string, int, int);
    //! Calculate spectral correlation
	//CImg<double> SpectralCorrelation(const GeoImage&, CImg<double> covariance=CImg<double>() );
	//! Calculate spectral covariance
	//CImg<double> SpectralCovariance(const GeoImage&);
	//! Spectral Matched Filter
	//GeoImage SMF(const GeoImage& image, std::string, CImg<double>);

} // namespace gip

#endif /* GIP_GEOALGORITHMS_H_ */
