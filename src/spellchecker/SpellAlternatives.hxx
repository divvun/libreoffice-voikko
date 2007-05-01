/* Openoffice.org-voikko: Finnish linguistic extension for OpenOffice.org
 * Copyright (C) 2005 - 2007 Harri Pitkänen <hatapitk@iki.fi>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 *********************************************************************************/

#ifndef _SPELLALTERNATIVES_HXX_
#define _SPELLALTERNATIVES_HXX_

#include <com/sun/star/linguistic2/XSpellAlternatives.hpp>
#include <com/sun/star/linguistic2/SpellFailure.hpp>
#include <cppuhelper/implbase1.hxx>

using namespace ::com::sun::star;
using namespace ::rtl;

namespace voikko {

class SpellAlternatives : public cppu::WeakImplHelper1<linguistic2::XSpellAlternatives> {
	public:
	OUString word;
	uno::Sequence<OUString> alternatives;

	virtual OUString SAL_CALL getWord() throw (uno::RuntimeException);
	virtual lang::Locale SAL_CALL getLocale() throw (uno::RuntimeException);
	virtual sal_Int16 SAL_CALL getFailureType() throw (uno::RuntimeException);
	virtual sal_Int16 SAL_CALL getAlternativesCount() throw (uno::RuntimeException);
	virtual uno::Sequence<OUString> SAL_CALL getAlternatives() throw (uno::RuntimeException);
};

}

#endif